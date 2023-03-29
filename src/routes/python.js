const { spawn } = require('child_process');
const express = require('express')
let router = express.Router()
const bodyParser = require('body-parser');
const path = require('path');

function runPythonScript(args) {
    return new Promise((resolve, reject) => {
        const pythonProcess = spawn('python', [`${path.join(__dirname, '../examples/clt-project/r3dm_translation.py')}`, `${JSON.stringify(args)}`]);
        let output = '';
    
        // capture the output of the Python process
        pythonProcess.stdout.on('data', (data) => {
          output += data.toString();
        });
    
        // handle any errors that occur
        pythonProcess.on('error', (err) => {
          reject(err);
        });
    
        // resolve the Promise with the output when the Python process exits
        pythonProcess.on('exit', (code) => {
          if (code !== 0) {
            reject(new Error(`Python process exited with code ${code}`));
          } else {
            resolve(output);
          }
        });
    });
}
    


function sendToPython(req,res){
    console.log(req.body)
    const command = [`${path.join(__dirname, '../examples/clt-project/min-k-partition.py')}`, `${JSON.stringify(req.body)}`];
    const childProcess = spawn('python',command);

    let outputData = ''; // Initialize output data variable

    childProcess.stdout.on('data', (data) => {
        outputData += data; 
    });
    childProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });
    childProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
        res.send(outputData); // Send output data back to client
      });


    // Send a response to the client
    //res.send('Received nCrv data');
}



router.post('/', function(req,res,next){
    sendToPython(req,res);
})

module.exports = router