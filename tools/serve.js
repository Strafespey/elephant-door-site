'use strict';
/*
 * Local preview: `npm run serve` (or `node tools/serve.js --port 8080`) serves the repo root the way GitHub
 * Pages does: /blog/3/ -> blog/3/index.html, /warlock -> warlock/index.html, /press.html-less paths, and 404.html
 * for anything missing. Dependency-free; Ctrl+C stops it.
 */
const fs = require('fs');
const http = require('http');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
const port = Number(args[args.indexOf('--port') + 1]) || 8080;
const TYPES = {
	'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
	'.json': 'application/json', '.xml': 'application/xml; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
	'.md': 'text/markdown; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
	'.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
};

function resolve(urlPath) {
	const clean = decodeURIComponent(urlPath.split('?')[0]).replace(/\/+$/, '') || '/';
	const abs = path.join(ROOT, clean);
	if (!abs.startsWith(ROOT)) return null;
	if (fs.existsSync(abs) && fs.statSync(abs).isDirectory()) {
		if (!urlPath.split('?')[0].endsWith('/')) return { redirect: clean + '/' };
		const index = path.join(abs, 'index.html');
		return fs.existsSync(index) ? { file: index } : null;
	}
	if (fs.existsSync(abs)) return { file: abs };
	if (fs.existsSync(abs + '.html')) return { file: abs + '.html' };
	return null;
}

http.createServer((req, res) => {
	const hit = resolve(req.url);
	if (hit && hit.redirect) {
		res.writeHead(301, { Location: hit.redirect });
		return res.end();
	}
	let file = hit && hit.file;
	let status = 200;
	if (!file) {
		file = path.join(ROOT, '404.html');
		status = 404;
		if (!fs.existsSync(file)) {
			res.writeHead(404, { 'Content-Type': 'text/plain' });
			return res.end('Not found');
		}
	}
	res.writeHead(status, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream' });
	fs.createReadStream(file).pipe(res);
}).listen(port, '127.0.0.1', () => console.log(`Serving ${ROOT} at http://localhost:${port}/ (Ctrl+C to stop)`));
