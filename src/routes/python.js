const { spawn } = require('child_process');
const express = require('express')
let router = express.Router()
const bodyParser = require('body-parser');
const path = require('path');
const WebSocket = require('ws');

let ws

function startPythonServer(res) {
  // console.log(__dirname, path.join(__dirname, '../examples/clt-project/min-k-partition.py'));
  const command = ['C:/Users/jacob/OneDrive/Documents/GitHub/compute.rhino3d.appserver/src/examples/clt-project/min-k-partition.py'] //[`${path.join(__dirname,'../examples/clt-project/min-k-partition.py')}`]
  const pythonProcess = spawn('python', command);

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`child process exited with code ${code}`);
  });

  // Wait for the WebSocket server to start before connecting the client
  const connectClient = () => {
    console.log('Connecting client...');

    ws = new WebSocket('ws://localhost:8765');

    ws.on('open', () => {
      res.send('Connection established!');
    });

    ws.on('message', (message) => {
      const data = JSON.parse(message);

      switch (data.type) {
        case 'stage':
          handleStageMessage(ws.res, data.message);
          break;
        case 'get':
          handleGetMessage(data.res, data);
          break;
        default:
          console.log(data);
      }
    });
  };
  
  const checkServer = setInterval(() => {
    const ws = new WebSocket('ws://localhost:8765');

    ws.on('open', () => {
      console.log('Server is running!');
      clearInterval(checkServer);
      connectClient();
    });

    ws.on('error', () => {
      console.log('Server is not running yet...');
    });
  }, 500);
}

function sendStageMessage(res, data) {
  const message = {
    action: 'stage',
    params: [data],
  };
  ws.send(JSON.stringify(message));
  ws.res = res;
}

function handleStageMessage(endpointRes, message) {
  endpointRes.send(message);
}

function sendGetMessage(res,index) {
  const message = {
    action: 'get',
    params: [index]
  };
  ws.send(JSON.stringify(message));
  ws.res = res;
}

function handleGetMessage(data) {
  const res = ws.res;
  console.log('Server applied partition:', data.message);
  res.send(data.body)
}

router.post('/startServer', function (req, res) {
  startPythonServer(res);
})

router.post('/stagePartitioning', function (req, res){
  sendStageMessage(res, req.body);
})

router.post('/getPartition', function (req, res){
  sendGetMessage(res,req);
})


module.exports = router