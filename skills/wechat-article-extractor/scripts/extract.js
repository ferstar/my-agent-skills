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
  return /^https?:\/\/(mp\.weixin\.qq\.com|weixin\.sogou\.com)\//.test(url);
}

function textBetween(source, patterns) {
  for (const pattern of patterns) {
    const match = source.match(pattern);
    if (match && match[1] != null) return match[1];
  }
  return null;
}

function numberBetween(source, patterns) {
  const text = textBetween(source, patterns);
  if (text == null) return null;
  const n = Number(text);
  return Number.isFinite(n) ? n : null;
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

function extractFromMeta($, html, url) {
  const title =
    $('.rich_media_title').first().text().trim() ||
    $('meta[property="og:title"]').attr('content') ||
    $('title').text().trim() ||
    null;

  const contentHtml = $('#js_content').html() || null;
  const publishTimestamp = numberBetween(html, [
    /var\s+ct\s*=\s*['"]?(\d{10})['"]?\s*;/,
    /d\.ct\s*=\s*['"]?(\d{10})['"]?/,
    /create_time\s*=\s*['"]?(\d{10})['"]?/
  ]);
  const publishTime = publishTimestamp ? new Date(publishTimestamp * 1000) : null;

  return {
    account_name:
      $('.profile_nickname').text().trim() ||
      $('.wx_follow_nickname').text().trim() ||
      null,
    account_alias: null,
    account_avatar:
      $('meta[property="og:image"]').attr('content') ||
      null,
    account_description: null,
    account_id: textBetween(html, [/user_name\s*=\s*['"]([^'"]+)['"]/, /var\s+user_name\s*=\s*['"]([^'"]+)['"]/]),
    account_biz: textBetween(html, [/\bbiz\s*=\s*['"]([^'"]+)['"]/, /var\s+biz\s*=\s*['"]([^'"]+)['"]/]),
    account_biz_number: null,
    account_qr_code: null,
    msg_title: title,
    msg_desc:
      $('meta[property="og:description"]').attr('content') ||
      $('meta[name="description"]').attr('content') ||
      (contentHtml ? htmlToText(contentHtml).slice(0, 140) : null),
    msg_content: contentHtml,
    msg_cover: $('meta[property="og:image"]').attr('content') || null,
    msg_author:
      $('meta[name="author"]').attr('content') ||
      $('#js_author_name').text().trim() ||
      null,
    msg_type: 'post',
    msg_has_copyright: $('#copyright_logo').text().includes('原创'),
    msg_publish_time: publishTime,
    msg_publish_time_str: publishTime ? dayjs(publishTime).format('YYYY/MM/DD HH:mm:ss') : null,
    msg_link: url || null,
    msg_source_url: textBetween(html, [/msg_source_url\s*=\s*['"]([^'"]+)['"]/]),
    msg_sn: url ? new URL(url).searchParams.get('sn') : null,
    msg_mid: url ? new URL(url).searchParams.get('mid') : null,
    msg_idx: url ? Number(new URL(url).searchParams.get('idx') || 0) || null : null
  };
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

  const $ = cheerio.load(html, { decodeEntities: false });
  const data = extractFromMeta($, html, url);

  if (data.account_id) {
    data.account_qr_code = `https://open.weixin.qq.com/qr/code?username=${data.account_id}`;
  }

  if (!data.msg_title || !data.msg_publish_time) {
    return getError(1001);
  }

  if (!config.shouldReturnContent) data.msg_content = null;

  return { code: 0, done: true, data };
}

module.exports = { extract, htmlToText };
