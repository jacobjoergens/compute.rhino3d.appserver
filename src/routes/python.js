const { spawn } = require('child_process');
const express = require('express')
let router = express.Router()

function runPythonScript() {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn('python', ['../examples/clt-project/r3dm_translation.py']);
    console.log('test')
    let stdout = '';
    let stderr = '';

    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(stderr);
      }
    });
  });
}
router.post('/', function() {
    runPythonScript()
})

module.exports = router