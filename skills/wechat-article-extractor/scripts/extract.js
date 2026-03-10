const dayjs = require('dayjs');
const cheerio = require('cheerio');
const errors = require('./errors');

const defaultConfig = {
  shouldReturnContent: true
};

function getError(code) {
  return { done: false, code, msg: errors[code] };
}

function normalizeUrl(input = '') {
  try {
    const url = new URL(input.replace(/&amp;/g, '&'));
    url.hash = '';
    return url.toString();
  } catch {
    return input.replace(/&amp;/g, '&');
  }
}

function isSupportedUrl(url) {
  return /^https?:\/\/mp\.weixin\.qq\.com\//.test(url);
}

function extractBetween(script, key) {
  const patterns = [
    new RegExp(`var\\s+${key}\\s*=\\s*['\"]([\\s\\S]*?)['\"]\\s*;`),
    new RegExp(`window\\.${key}\\s*=\\s*['\"]([\\s\\S]*?)['\"]\\s*;`),
    new RegExp(`${key}\\s*:\\s*['\"]([\\s\\S]*?)['\"]`)
  ];
  for (const pattern of patterns) {
    const match = script.match(pattern);
    if (match && match[1] != null) return match[1];
  }
  return null;
}

function extractNumber(script, key) {
  const patterns = [
    new RegExp(`var\\s+${key}\\s*=\\s*(\\d+)\\s*;`),
    new RegExp(`window\\.${key}\\s*=\\s*(\\d+)\\s*;`),
    new RegExp(`${key}\\s*:\\s*(\\d+)`)
  ];
  for (const pattern of patterns) {
    const match = script.match(pattern);
    if (match && match[1] != null) return Number(match[1]);
  }
  return null;
}

function htmlToText(html = '') {
  return html
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/\s+\n/g, '\n')
    .replace(/\n\s+/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .trim();
}

function detectError(html) {
  if (!html) return 1003;
  if (html.includes('访问过于频繁') && !html.includes('js_content')) return 1004;
  if (html.includes('链接已过期') && !html.includes('js_content')) return 2002;
  if (html.includes('该内容已被发布者删除')) return 2005;
  if (html.includes('此内容因违规无法查看')) return 2006;
  if (html.includes('此帐号已被屏蔽') && !html.includes('id="js_content"')) return 2012;
  return null;
}

async function fetchHtml(url) {
  const response = await fetch(url, {
    headers: {
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
      'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8'
    },
    redirect: 'follow'
  });

  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return await response.text();
}

async function extract(input, options = {}) {
  if (!input) return getError(2001);

  const config = { ...defaultConfig, ...options };
  let url = options.url ? normalizeUrl(options.url) : null;
  let html = input;

  if (/^http/.test(input)) {
    url = normalizeUrl(input);
    if (!isSupportedUrl(url)) return getError(2009);
    try {
      html = await fetchHtml(url);
    } catch {
      return getError(1002);
    }
  }

  const errorCode = detectError(html);
  if (errorCode) return getError(errorCode);
  if (!html.includes('js_content') && !html.includes('rich_media_title')) return getError(1000);

  const $ = cheerio.load(html, { decodeEntities: false });
  const scripts = ($('script').map((_, el) => $(el).html() || '').get()).join('\n');

  const title =
    $('.rich_media_title').first().text().trim() ||
    $('meta[property="og:title"]').attr('content') ||
    extractBetween(scripts, 'msg_title');

  const author =
    $('meta[name="author"]').attr('content') ||
    $('#js_author_name').text().trim() ||
    extractBetween(scripts, 'nickname');

  const contentHtml = config.shouldReturnContent
    ? ($('#js_content').html() || null)
    : null;

  const publishTimestamp =
    extractNumber(scripts, 'ct') ||
    extractNumber(scripts, 'create_time');

  const publishTime = publishTimestamp ? new Date(publishTimestamp * 1000) : null;
  const publishTimeStr = publishTime ? dayjs(publishTime).format('YYYY/MM/DD HH:mm:ss') : null;

  const description =
    $('meta[property="og:description"]').attr('content') ||
    $('meta[name="description"]').attr('content') ||
    (contentHtml ? htmlToText(contentHtml).slice(0, 140) : null);

  const cover =
    $('meta[property="og:image"]').attr('content') ||
    extractBetween(scripts, 'msg_cdn_url');

  const accountName =
    $('.profile_nickname').text().trim() ||
    $('.wx_follow_nickname').text().trim() ||
    extractBetween(scripts, 'nickname');

  const accountId = extractBetween(scripts, 'user_name');
  const biz = extractBetween(scripts, 'biz');

  const data = {
    account_name: accountName || null,
    account_alias: null,
    account_avatar: extractBetween(scripts, 'ori_head_img_url') || extractBetween(scripts, 'hd_head_img') || null,
    account_description: null,
    account_id: accountId || null,
    account_biz: biz || null,
    account_biz_number: null,
    account_qr_code: accountId ? `https://open.weixin.qq.com/qr/code?username=${accountId}` : null,
    msg_title: title || null,
    msg_desc: description || null,
    msg_content: contentHtml,
    msg_cover: cover || null,
    msg_author: author || null,
    msg_type: 'post',
    msg_has_copyright: $('#copyright_logo').text().includes('原创'),
    msg_publish_time: publishTime,
    msg_publish_time_str: publishTimeStr,
    msg_link: url || null,
    msg_source_url: extractBetween(scripts, 'msg_source_url') || null,
    msg_sn: url ? new URL(url).searchParams.get('sn') : null,
    msg_mid: url ? new URL(url).searchParams.get('mid') : null,
    msg_idx: url ? Number(new URL(url).searchParams.get('idx') || 0) || null : null
  };

  if (!data.msg_title || !data.msg_publish_time) return getError(1001);

  return { code: 0, done: true, data };
}

module.exports = { extract, htmlToText };
