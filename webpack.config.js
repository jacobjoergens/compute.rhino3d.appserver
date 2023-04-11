const path = require('path');

module.exports = {
    mode: 'development',
    entry: './src/examples/clt-project/script.js',
    output: {
      filename: 'bundle.js',
      path: path.resolve(__dirname, './src/examples/clt-project'),
    },
  };
  