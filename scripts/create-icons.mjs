import sharp from 'sharp';
const svg=Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512"><rect width="512" height="512" fill="#315e3a"/><text x="256" y="332" text-anchor="middle" font-family="Arial,sans-serif" font-size="250" font-weight="bold" fill="white">z.</text></svg>');
await Promise.all([192,512].map(size=>sharp(svg).resize(size,size).png().toFile(`public/icon-${size}.png`)));
