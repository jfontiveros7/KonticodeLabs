const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
const fetch = require("node-fetch");

async function run(mode) {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage("Open a file first.");
    return;
  }

  const selection = editor.document.getText(editor.selection) || editor.document.getText();
  const promptPath = path.join(__dirname, "prompts", `${mode}.txt`);
  const basePrompt = fs.readFileSync(promptPath, "utf8");

  const finalPrompt = `${basePrompt}\n\n---\nCODE:\n${selection}`;

  const apiKey = process.env.OPENAI_API_KEY;

  if (!apiKey) {
    vscode.window.showErrorMessage("OPENAI_API_KEY is missing. Set it in your environment variables.");
    return;
  }

  vscode.window.showInformationMessage(`Coding Agent running: ${mode}`);

  // Call OpenAI API
  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: basePrompt },
        { role: "user", content: selection }
      ]
    })
  });

  const data = await response.json();

  const output = data.choices?.[0]?.message?.content || "No response from model.";

  const panel = vscode.window.createWebviewPanel(
    "codingAgent",
    `Coding Agent — ${mode}`,
    vscode.ViewColumn.Beside,
    {}
  );

  panel.webview.html = `<pre>${output}</pre>`;
}

module.exports = { run };