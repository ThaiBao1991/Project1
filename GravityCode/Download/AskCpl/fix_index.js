const fs = require('fs');
const path = require('path');

const targetDir = 'C:\\Users\\games\\Desktop\\Query_Gemini';
const sessionPath = path.join(targetDir, 'session.json');
const indexPath = path.join(targetDir, 'index.html');

if (!fs.existsSync(sessionPath)) {
    console.error("session.json not found!");
    process.exit(1);
}

const session = JSON.parse(fs.readFileSync(sessionPath, 'utf8'));

// Read all day_X.html files
const files = fs.readdirSync(targetDir);
const dayFiles = files.filter(f => /^day_\d+\.html$/.test(f));

const daysArray = [];

for (const file of dayFiles) {
    const match = file.match(/^day_(\d+)\.html$/);
    if (match) {
        const dayNum = parseInt(match[1], 10);
        const stat = fs.statSync(path.join(targetDir, file));
        
        daysArray.push({
            dayNum: dayNum,
            day: `Day ${dayNum}`,
            filename: `${session.folderName}/${file}`,
            timestamp: stat.mtime.toISOString()
        });
    }
}

// Sort by day number
daysArray.sort((a, b) => a.dayNum - b.dayNum);

// Remove dayNum for final JSON
const finalDays = daysArray.map(d => ({
    day: d.day,
    filename: d.filename,
    timestamp: d.timestamp
}));

session.days = finalDays;
session.totalSaved = finalDays.length;
if (finalDays.length > 0) {
    session.lastDay = daysArray[daysArray.length - 1].dayNum;
}

fs.writeFileSync(sessionPath, JSON.stringify(session, null, 2), 'utf8');
console.log(`Updated session.json with ${finalDays.length} days.`);

// Rebuild index.html
let html = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Saved Data - ${session.agentName}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; background: #f9f9f9; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 2rem; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 8px; }
        h1 { color: #333; text-align: center; }
        .info { text-align: center; color: #666; margin-bottom: 2rem; }
        ul { list-style: none; padding: 0; }
        li { margin: 10px 0; padding: 10px; border: 1px solid #eee; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
        li:hover { background: #f1f1f1; }
        a { text-decoration: none; color: #0066cc; font-weight: bold; font-size: 1.1em; }
        a:hover { text-decoration: underline; }
        .time { color: #999; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📑 Saved Data - ${session.agentName}</h1>
        <div class="info">
            <p><strong>Thư mục:</strong> ${session.folderName} | <strong>Tổng số bài:</strong> ${finalDays.length}</p>
            <p><em>Cập nhật lần cuối: ${new Date().toLocaleString('vi-VN')}</em></p>
        </div>
        <ul>`;

for (const d of finalDays) {
    // filename might contain "Query_Gemini/day_x.html", we just want "day_x.html" for relative link
    const relFile = d.filename.split('/').pop();
    const timeStr = new Date(d.timestamp).toLocaleString('vi-VN');
    html += `\n            <li><a href="${relFile}" target="_blank">${d.day}</a> <span class="time">${timeStr}</span></li>`;
}

html += `
        </ul>
    </div>
</body>
</html>`;

fs.writeFileSync(indexPath, html, 'utf8');
console.log(`Updated index.html with ${finalDays.length} links.`);
