// 分支节点图（BRANCHING.md）。每个节点一段独立视频；choice 节点播放可循环的等待镜头并显示选项。
// 史实结果不因选择改变：选择决定先看哪处现场、结尾强调哪一面。
window.GRAPH = {
  start: "trunk",
  bgm: "clips/bgm.m4a",
  nodes: {
    trunk: { clip: "clips/trunk.mp4", next: "choice1" },
    choice1: {
      loop: "clips/loop1.mp4",
      eyebrow: "选择 1 · 两处现场",
      title: "先去哪处现场？",
      copy: "两根烟柱，相距不到一英里。你先看到哪一处，就先读哪一处的记录。",
      timeout: 15,
      options: [
        { key: "A", label: "第一处 · 约三个街区外", hint: "残骸旁的搜救", set: { site: "first" }, next: "siteA" },
        { key: "B", label: "第二处 · 南面不到一英里", hint: "无法抵达的现场", set: { site: "second" }, next: "siteB" },
      ],
    },
    siteA: { clip: "clips/site_a.mp4", next: "converge" },
    siteB: { clip: "clips/site_b.mp4", next: "converge" },
    converge: {
      clip: "clips/converge.mp4",
      next: "dawn",
      // 汇合段按此前的选择补一句下沿字幕
      note: {
        first: "你先看到的就是这里：车队整夜驶向的第一处坠机点。",
        second: "你先读了第二处现场。车队此刻驶向的，是第一处。",
      },
    },
    dawn: { clip: "clips/dawn.mp4", next: "choice2" },
    choice2: {
      loop: "clips/loop2.mp4",
      eyebrow: "选择 2 · 结尾视角",
      title: "结尾看哪一面？",
      copy: "同一个早晨，三种记录。",
      timeout: 15,
      options: [
        { key: "1", label: "任务与救援", hint: "车队撤回体育场", set: { ending: "operation" }, next: "endA" },
        { key: "2", label: "城市与平民", hint: "没有统一的伤亡数字", set: { ending: "city" }, next: "endB" },
        { key: "3", label: "政策后果", hint: "次年三月撤军", set: { ending: "aftermath" }, next: "endC" },
      ],
    },
    endA: { clip: "clips/end_a.mp4", next: "card" },
    endB: { clip: "clips/end_b.mp4", next: "card" },
    endC: { clip: "clips/end_c.mp4", next: "card" },
    card: { end: true },
  },
  labels: {
    site: { first: "第一处现场", second: "第二处现场" },
    ending: { operation: "任务与救援", city: "城市与平民", aftermath: "政策后果" },
  },
  coda: "选择改变的是你先看到什么、结尾强调什么；历史结果不变。来源：美国陆军战后报告、联合国 S/26738、《华盛顿邮报》、美国国务院史料办公室。",
};
