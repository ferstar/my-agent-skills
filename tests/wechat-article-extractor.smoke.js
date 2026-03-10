const assert = require('node:assert/strict');
const { extract } = require('../skills/wechat-article-extractor/scripts/extract');

const TEST_URL = 'https://mp.weixin.qq.com/s/TpmrSdx13CqApwN3iZQVew?scene=1&click_id=89';

(async () => {
  const result = await extract(TEST_URL);

  assert.equal(result.done, true, 'extract should succeed');
  assert.equal(result.code, 0, 'code should be 0');
  assert.ok(result.data, 'data should exist');
  assert.equal(result.data.msg_title, '打造高效易用的Agent Skill', 'title should match');
  assert.ok(result.data.account_name, 'account_name should exist');
  assert.ok(result.data.msg_publish_time_str, 'publish time should exist');
  assert.ok(result.data.msg_content && result.data.msg_content.length > 200, 'content should exist');

  console.log(JSON.stringify({
    ok: true,
    title: result.data.msg_title,
    account: result.data.account_name,
    time: result.data.msg_publish_time_str
  }, null, 2));
})();
