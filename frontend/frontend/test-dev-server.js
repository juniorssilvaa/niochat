#!/usr/bin/env node

const { spawn } = require('child_process');
const http = require('http');

console.log('🚀 Testando servidor de desenvolvimento...');

// Iniciar servidor de desenvolvimento
const devServer = spawn('npm', ['run', 'dev'], {
  stdio: 'pipe',
  shell: true
});

let serverReady = false;

devServer.stdout.on('data', (data) => {
  const output = data.toString();
  console.log(output);
  
  if (output.includes('Local:') && output.includes('http://localhost:')) {
    serverReady = true;
    console.log('✅ Servidor iniciado com sucesso!');
    
    // Testar se o servidor responde
    setTimeout(() => {
      testServer();
    }, 2000);
  }
});

devServer.stderr.on('data', (data) => {
  const error = data.toString();
  console.error('❌ Erro:', error);
  
  if (error.includes('Invalid hook call') || error.includes('useRef')) {
    console.error('🔴 ERRO: Problema com React hooks detectado!');
    process.exit(1);
  }
});

function testServer() {
  const options = {
    hostname: 'localhost',
    port: 8012,
    path: '/',
    method: 'GET',
    timeout: 5000
  };

  const req = http.request(options, (res) => {
    console.log(`✅ Servidor respondendo: ${res.statusCode}`);
    console.log('🎉 Frontend funcionando corretamente!');
    devServer.kill();
    process.exit(0);
  });

  req.on('error', (err) => {
    console.error('❌ Erro ao conectar com servidor:', err.message);
    devServer.kill();
    process.exit(1);
  });

  req.on('timeout', () => {
    console.error('❌ Timeout ao conectar com servidor');
    devServer.kill();
    process.exit(1);
  });

  req.end();
}

// Timeout de 30 segundos
setTimeout(() => {
  if (!serverReady) {
    console.error('❌ Timeout: Servidor não iniciou em 30 segundos');
    devServer.kill();
    process.exit(1);
  }
}, 30000);

