const { extract } = require('./scripts/extract');

(async () => {
  const url = process.argv[2];
  if (!url) {
    console.error('Usage: node test.js <mp.weixin url>');
    process.exit(1);
  }
  const result = await extract(url);
  if (!result.done) {
    console.log(JSON.stringify(result, null, 2));
    process.exit(2);
  }
  const data = result.data || {};
  console.log(JSON.stringify({
    title: data.msg_title,
    author: data.msg_author,
    publishTime: data.msg_publish_time_str,
    desc: data.msg_desc,
    contentPreview: (data.msg_content || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 300)
  }, null, 2));
})();
