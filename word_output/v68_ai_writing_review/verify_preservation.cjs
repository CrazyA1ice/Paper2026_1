const fs = require('fs');
const path = require('path');
const base = 'C:/Users/Quant/.codex/plugins/cache/openai-curated-remote/avoid-ai-writing/3.29.0/skills';
const engine = require(base + '/ai-writing-detector/scripts/patterns.js');
const {validate, formatResult} = require(base + '/preservation-verifier/scripts/validate.js');
const read = name => fs.readFileSync(path.join(__dirname, name), 'utf8');
const detector = {analyzeText: text => engine.analyzeText(text, {contextMode: 'technical'})};
const result = validate(read('preservation_before.md'), read('preservation_after.md'), {detector});
fs.writeFileSync(path.join(__dirname, 'preservation_result.json'), JSON.stringify(result, null, 2));
for (const label of ['before', 'after']) {
  fs.writeFileSync(path.join(__dirname, 'detector_' + label + '.json'),
    JSON.stringify(detector.analyzeText(read('scan_' + label + '.txt')), null, 2));
}
process.stdout.write(formatResult(result) + '\n');
if (!result.ok) process.exitCode = 1;
