const film = document.querySelector("#film");
const startVeil = document.querySelector("#start-veil");
const choiceVeil = document.querySelector("#choice-veil");
const choicePanel = document.querySelector("#choice-panel");
const statusLine = document.querySelector("#player-status");

const FIRST_PROMPT = 35.5;
// Wait until every in-frame ending option has finished appearing.
const SECOND_PROMPT = 58.5;

let started = false;
let firstChoice = null;
let endingChoice = null;
let firstWaitShown = false;
let secondWaitShown = false;

const branchCopy = {
  site1: {
    id: "SC02A1",
    eyebrow: "档案 A · 第一处现场",
    title: "救援如何抵达",
    copy: "第一处坠机点距目标约三个街区。选读这份现场记录后，回到共同时间线。",
  },
  site2: {
    id: "SC02A2",
    eyebrow: "档案 B · 第二处现场",
    title: "增援如何调动",
    copy: "第二处坠机点在第一处以南不到一英里。选读这份现场记录后，回到共同时间线。",
  },
};

const endingCopy = {
  operation: {
    id: "SC04A",
    title: "任务与救援",
    copy: "聚焦抓捕行动如何转成救援，以及记录中可以确认的行动结果。",
  },
  city: {
    id: "SC04B",
    title: "城市与平民",
    copy: "聚焦城市伤亡记录的缺口，不把不同估计写成确定总数。",
  },
  aftermath: {
    id: "SC04C",
    title: "政策后果",
    copy: "聚焦国际介入背景，以及美国之后宣布撤军的时间线。",
  },
};

function showPanel(eyebrow, title, copy, buttons, three = false) {
  choicePanel.replaceChildren();
  const label = document.createElement("p");
  label.className = "eyebrow";
  label.textContent = eyebrow;
  const heading = document.createElement("h1");
  heading.textContent = title;
  const description = document.createElement("p");
  description.className = "copy";
  description.textContent = copy;
  const controls = document.createElement("div");
  controls.className = `choices${three ? " three" : ""}`;
  controls.append(...buttons);
  choicePanel.append(label, heading, description, controls);
  choiceVeil.hidden = false;
}

function makeButton(label, onClick, primary = false) {
  const button = document.createElement("button");
  button.textContent = label;
  if (primary) button.className = "primary";
  button.addEventListener("click", onClick, { once: true });
  return button;
}

function showFirstChoice() {
  firstWaitShown = true;
  film.pause();
  film.currentTime = FIRST_PROMPT;
  statusLine.textContent = "暂停中 · 请选择先读哪处现场记录";
  showPanel("等待选择 · 档案次序", "先看哪处现场？", "两条档案路径会在 01:55 汇合。", [
    makeButton("A · 第一处救援记录", () => selectFirst("site1")),
    makeButton("B · 第二处增援记录", () => selectFirst("site2")),
  ]);
}

function selectFirst(key) {
  firstChoice = key;
  const branch = branchCopy[key];
  statusLine.textContent = `已选择 ${branch.id} · 等待继续`;
  showPanel(branch.eyebrow, branch.title, branch.copy, [
    makeButton("继续到共同时间线 · 01:55", continueCommon, true),
  ]);
}

function continueCommon() {
  firstWaitShown = false;
  choiceVeil.hidden = true;
  statusLine.textContent = `已选择 ${branchCopy[firstChoice].id} · 继续播放`;
  film.currentTime = 40.02;
  film.play();
}

function showEndingChoice() {
  secondWaitShown = true;
  film.pause();
  film.currentTime = SECOND_PROMPT;
  statusLine.textContent = "暂停中 · 请选择片尾视角";
  showPanel("等待选择 · 片尾视角", "结尾强调哪一面？", "", [
    makeButton("任务与救援", () => selectEnding("operation")),
    makeButton("城市与平民", () => selectEnding("city")),
    makeButton("政策后果", () => selectEnding("aftermath")),
  ], true);
}

function selectEnding(key) {
  endingChoice = key;
  const ending = endingCopy[key];
  statusLine.textContent = `已选择 ${ending.id} · 样片结束`;
  showPanel(`片尾路径 · ${ending.id}`, ending.title, ending.copy, [
    makeButton("重新观看", restart, true),
  ]);
}

function restart() {
  firstChoice = null;
  endingChoice = null;
  firstWaitShown = false;
  secondWaitShown = false;
  choiceVeil.hidden = true;
  startVeil.hidden = false;
  statusLine.textContent = "互动模式 · 60 秒样片";
  film.currentTime = 0;
  film.pause();
  started = false;
}

document.querySelector("#start-button").addEventListener("click", () => {
  started = true;
  startVeil.hidden = true;
  statusLine.textContent = "播放中 · 将在选择点暂停";
  film.play().catch(() => {
    started = false;
    startVeil.hidden = false;
    statusLine.textContent = "无法播放视频；请在本地浏览器打开 player.html";
  });
});

film.addEventListener("timeupdate", () => {
  if (!started) return;
  if (!firstChoice && !firstWaitShown && film.currentTime >= FIRST_PROMPT) {
    showFirstChoice();
    return;
  }
  if (firstChoice && !endingChoice && !secondWaitShown && film.currentTime >= SECOND_PROMPT) {
    showEndingChoice();
    return;
  }
});

film.addEventListener("ended", () => {
  if (!endingChoice) showEndingChoice();
});
