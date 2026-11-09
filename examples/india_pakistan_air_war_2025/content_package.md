# 试跑内容包：2025 年 5 月印巴空战

**版本：** 0.3（双视角重建版，飞行员对飞行员）  
**日期：** 2026-11-01  
**形态：** 双视角重建影游，两名合成角色飞行员交替推进  
**建议时长：** 12–15 分钟  
**状态：** 桌面审阅稿；不是成片剧本。装备视觉参考见 [equipment_reference.md](equipment_reference.md)，剧情数据见 [story.json](story.json)。

## 项目 brief

**主题：** 2025 年 5 月 7 日凌晨的印巴超视距空战，以及 5 月 7–10 日冲突中的空中行动。  
**片名（暂定）：** 《五十二分钟》  
**玩家身份：** 玩家不扮演真实人物，而是在两名**合成角色**飞行员之间切换。两人隔着边境、相距上百公里，彼此从未见面，也不知道对方是谁。

| | 法拉兹 | 罗汉 |
| --- | --- | --- |
| **所属** | 巴基斯坦空军，J-10C 飞行员，驻卡姆拉 | 印度空军，"阵风"飞行员，驻前线基地 |
| **呼号（虚构）** | 利爪 2 | 游隼 3 |
| **座舱里看得到** | 引导员的数据链指示、导弹离架、目标航迹 | 打击航线、雷达告警、僚机的无线电 |
| **座舱里看不到** | 自己发射的导弹最后打中了什么 | 威胁从多远、从哪里来 |
| **牵挂的人** | 妹妹，住在穆扎法拉巴德 | 母亲，住在查谟 |

**叙事承诺：** 选择决定玩家在每个关键时刻跟随谁、看见战场的哪一半。真实战果、伤亡和双方的声明不因选择而改变。两个角色各自只知道自己那一侧的情况，双方战损的争议放到片尾的来源卡里统一交代。  
**改编模式：** 适度戏剧化，并明确标注。

- 全片以重建演示为主，画面角落常驻"重建演示"标签。
- 两个角色、他们的家人和僚机都是虚构的，由公开报道综合而成，标注为"合成角色"或"虚构人物"。
- 所有对白和无线电通话都是创作内容，字幕标为"创作对白"。法拉兹说乌尔都语和英语，罗汉说印地语和英语，配中文字幕。
- **合成角色不对任何具体的击落负责。** 法拉兹会发射导弹，但始终不知道是否命中；罗汉的僚机失联，但不对应任何一处真实坠机点。"谁击落了谁"只能由片尾的来源卡回答。
- 真实官员只在片尾声明卡中出现，内容为转述并标明出处，不为其编写台词。

选择这一形态，是因为这场空战双方隔着上百公里交战、互不越境，每一方都只看到战场的一半。让玩家在两个座舱之间切换，既能把驾驶舱、雷达屏和装备拍得足够近，又能把"谁也看不到全貌"的战争迷雾变成玩法本身。

## 角色设定

以下人物全部虚构。姓名选用两国常见的名字，上线前需检索确认不与已公开的真实参战人员重名。

### 法拉兹·马利克（巴方）
- **身份：** 巴基斯坦空军少校，32 岁，J-10C 飞行员，所在中队驻卡姆拉的明哈斯基地。
- **出身：** 白沙瓦人。父亲是空军地勤技师，在机库里干了一辈子，法拉兹从小在基地家属区长大。
- **家人：** 妹妹萨娜，28 岁，在穆扎法拉巴德一所中学教书。法拉兹每次值夜班前都会给她发一条语音消息，内容几乎不变："睡吧，我在天上。"
- **性格：** 话少，讲规矩，相信数据链和屏幕上的数字。
- **贯穿全片的问题：** 他发射了导弹，屏幕上的航迹消失了，但他不知道那意味着什么。战后中队被公开记功，他自己的任务记录上却写着"结果未确认"。
- **随身物品：** 父亲留下的一个扳手形状的旧钥匙扣，挂在飞行服拉链上。

### 罗汉·巴蒂亚（印方）
- **身份：** 印度空军少校，34 岁，"阵风"飞行员。
- **出身：** 斋浦尔人，家里第一个参军的人。
- **家人：** 母亲住在查谟，是退休的小学老师，父亲早逝。罗汉调到前线基地后，母亲坚持不搬家。
- **僚机：** 尼尔·塔帕上尉，呼号"游隼 4"，罗汉在飞行学院带过的学弟，爱开玩笑。尼尔是虚构人物，不对应任何真实坠机或真实飞行员。
- **性格：** 冷静、要强，习惯把任务前的紧张藏在玩笑后面。
- **贯穿全片的问题：** 打击任务完成了，回来的路上却有一个呼号再也没有回答。他知道的只有上级的一句"不谈损失"。
- **随身物品：** 母亲塞给他的一小包糖，他每次出任务都带着，从来不吃。

### 对称关系
两人的家人分别住在克什米尔控制线两侧，都处在这几天炮击和空袭的阴影里。萨娜所在城市的一座清真寺在 5 月 7 日被打击；罗汉母亲所在的查谟在 5 月 8 日和 10 日的夜里传出爆炸声。两条家人线只用电话和语音消息呈现，不虚构家人的伤亡。

## 史实卡片

状态说明：**已证实** = 多个独立来源一致；**归属陈述** = 只能写成"某方称"；**争议** = 各方说法冲突。

| ID | 可用陈述 | 状态 | 来源 |
| --- | --- | --- | --- |
| F01 | 2025 年 4 月 22 日，帕哈尔加姆附近发生袭击，26 名平民遇难，多数为游客。巴基斯坦否认与袭击有关。 | 已证实（伤亡）；归属争议 | S01 S02 |
| F02 | 印度随后宣布暂停《印度河水条约》等措施；巴方关闭领空并暂停贸易，称暂停条约是"战争行为"。 | 已证实 | S03 S04 |
| F03 | 5 月 7 日 01:05–01:30（印度时间），印度发动"辛杜尔行动"，打击巴基斯坦及巴控克什米尔的 9 处地点。印方称打击对象是恐怖组织设施，巴方称打击对象是平民区和清真寺。 | 已证实（时间、目标数）；目标性质争议 | S05 S06 S07 |
| F04 | 印方旁遮普方向的目标由空军打击。据《今日印度》援引消息人士，"阵风"挂载了 SCALP 导弹和 HAMMER 炸弹；陆军使用了 M982"神剑"制导炮弹和巡飞弹。 | 归属陈述 | S08 S09 |
| F05 | 随后爆发空战。据《空军月刊》，参战飞机超过 114 架（印方 72 架、巴方 42 架）。双方都没有越境，交战距离有时超过 100 公里。 | 归属陈述（架数） | S10 S11 |
| F06 | 据一名巴方高级军官称，空战持续约 52 分钟。 | 归属陈述 | S10 |
| F07 | 巴方使用 J-10C 发射 PL-15 远程空空导弹，这是该导弹首次实战使用。印度境内多处发现 PL-15 残骸。 | 已证实（残骸）；击落归因见 F09 | S12 S13 |
| F08 | 巴方《黎明报》称，6 月 6 日巴基斯坦空军把战果归于驻卡姆拉明哈斯基地的第 15 中队"眼镜蛇"（装备 J-10C），该中队 20 架飞机中有 18 架参与拦截。 | 归属陈述 | S14 |
| F09 | 5 月 8 日，一名美国官员对路透社称，"高度确信"巴方 J-10 至少击落 2 架印度战机；另一名官员评估其中 1 架是"阵风"。 | 归属陈述（匿名官员） | S13 |
| F10 | 《华盛顿邮报》识别出 5 月 7 日的 3 处坠机点：巴廷达阿卡利亚卡兰的"阵风"、潘波尔的幻影 2000，以及阿克努尔的一处（可能是米格-29）。巴廷达的坠机据报道造成两名旁观者死亡。 | 已证实（坠机点）；机型为媒体识别 | S15 S16 |
| F11 | 巴方最初称击落 5 架（3 架"阵风"、米格-29、苏-30MKI 各 1 架）和 1 架"苍鹭"无人机；总理谢里夫后来称 6 架，又称其中 4 架是"阵风"。 | 归属陈述 | S17 S18 |
| F12 | 5 月 11 日，印度空军称"损失是战斗的一部分"，所有飞行员均已回家，但没有给出细节。5 月 31 日，国防参谋长乔汉承认印方有战机损失，但否认巴方击落 6 架的说法。 | 已证实（声明本身） | S19 S20 |
| F13 | 法国空天军参谋长称，他"看到了证据"，证明有 3 架飞机被击落：1 架"阵风"、1 架幻影 2000、1 架苏霍伊。 | 归属陈述 | S21 |
| F14 | 2025 年 8 月，印度空军参谋长称用 S-400 击落 5 架巴方战机和 1 架预警机。《空军月刊》称这一说法缺乏佐证。巴方否认。 | 争议 | S10 |
| F15 | 5 月 8 日，印方称用 S-400 拦截了巴方的无人机和导弹，这是该系统首次实战使用；巴方否认发动这些袭击。印方称巴方动用了 300–400 架土耳其产无人机，巴方称击落了数十架以色列产"哈洛普"。 | 双方各自声明 | S22 S23 S24 |
| F16 | 5 月 10 日凌晨，印方打击巴方多处空军基地，努尔汗基地于 02:09 遭打击。卫星图显示多处机库、跑道受损；博拉里基地一架萨博 2000"爱立眼"预警机受损，巴方称已修复。 | 已证实（卫星图）；具体战损部分为归属陈述 | S25 S26 S10 |
| F17 | 巴方军方确认 5 月 10 日有 6 名空军人员死亡，其中博拉里 5 人。 | 已证实（巴方确认） | S26 |
| F18 | 巴方随即发起"坚固之墙"行动（Bunyan-um-Marsoos），称打击了印方 26 处军事目标。印方承认乌汉普尔、帕坦科特、阿丹普尔、布杰四处基地受到有限损伤；《纽约时报》称卫星图未能清楚显示巴方声称的大部分破坏。 | 双方各自声明 + 第三方卫星分析 | S27 S28 |
| F19 | 停火于 5 月 10 日 17:00（印度时间）生效，先由特朗普在社交媒体宣布。印方称停火是双方军方直接谈成的。 | 已证实 | S29 S30 |
| F20 | 据各自政府统计，印方 21 名平民、8 名军人和准军事人员死亡；巴方 40 名平民、13 名军人死亡。 | 归属陈述（各方统计） | S31 S32 |
| F21 | 美国国会美中经济与安全审查委员会 2025 年报告称，巴方取得了军事上的成功，这是 J-10、PL-15、HQ-9 等中国现代装备首次实战使用。 | 归属陈述 | S33 |
| S34 | The Times of India, "'I love you': IAF martyr Sergeant Surendra Moga's wife clutches his uniform as family bids final goodbye" (2025-05-12) <https://timesofindia.indiatimes.com/city/pune/i-love-you-iaf-martyr-sergeant-surendra-mogas-wife-clutches-his-uniform-as-family-bids-final-goodbye/articleshow/121095633.cms> | F22 |
| S35 | The Express Tribune, "Pakistan downs five Indian fighter jets in retaliation for India's missile attack: security sources" (2025-05-07) <https://tribune.com.pk/story/2544343/indian-missile-strikes-hit-muzaffarabad-kotli-and-bahawalpur-amid-escalating-tensions> | F23 |
| S36 | Reuters, "India strikes Pakistan over Kashmir tourist killings" (2025-05-06) <https://www.reuters.com/world/asia-pacific/multiple-loud-explosions-heard-pakistani-kashmir-reuters-witness-2025-05-06/> | F23 |
| S37 | The Indian Express, "8 missiles targeted at Jammu intercepted, blackouts from Punjab to Rajasthan" (2025-05-08) <https://indianexpress.com/article/india/missiles-targeted-jammu-blackout-punjab-rajasthan-9991390/> | F24 |
| S38 | Al Jazeera, "Five killed by Pakistani shelling in Jammu region: Reports" (2025-05-10) <https://www.aljazeera.com/news/liveblog/2025/5/10/india-pakistan-live-pakistan-airbases-targeted-as-blasts-rock-north-india?update=3699418> | F24 |
| F23 | 巴方称，5 月 7 日印方对穆扎法拉巴德的萨伊德纳·比拉尔清真寺和科特利的阿巴斯清真寺的打击造成 5 名平民死亡；印方称这些地点与恐怖组织有关。 | 双方各自声明 | S35 S36 |
| F24 | 5 月 8 日夜，查谟传出多次爆炸，印方称拦截了 8 枚针对查谟的巴方导弹；5 月 10 日，地方官员称拉焦里、蓬奇、查谟三个地区至少 5 人死于巴方炮击。 | 归属陈述（印方及地方官员） | S37 S38 |
| F22 | 巴方空袭乌汉普尔空军基地后，一名印度空军士官阵亡。 | 已证实（印方媒体报道、家属确认） | S34 S28 |

### 史实边界

- **印方战损数量不写成定论。** 可以写："印方承认有损失但未公布数字；独立评估认为至少 3–4 架。"不能写"巴方击落 6 架"或"印方损失 X 架"。
- **巴方战损同样不写成定论。** F14 只能作为印方声明呈现，并附上"缺乏公开证据"的说明。
- **5 月 7 日的打击目标性质有争议。** 印方称是"恐怖分子基础设施"，巴方称是平民区和清真寺。两种说法并列，各自标明出处。
- **不重演帕哈尔加姆袭击。** 只用标题卡和遇难人数交代，不拍摄或生成袭击画面。
- **所有空战镜头都是重建。** 雷达屏幕、驾驶舱、导弹轨迹的具体时间、距离和机位均属示意；画面上始终显示"重建演示"标签。
- **合成角色不对应真实坠机。** 罗汉的僚机尼尔（"游隼 4"）是虚构的，不对应巴廷达、潘波尔或阿克努尔的任何一处坠机点；法拉兹发射的导弹始终"结果未确认"，不宣称任何一次具体击落。
- **家人线不虚构伤亡。** 萨娜和罗汉母亲都平安；她们所在城市遭受的打击和炮击按 F23、F24 的来源呈现，并标明是哪一方的说法。
- **不使用真实机号和真实呼号。** 巴方公布的"阵风"机号、呼号属于单方声明，只能出现在片尾来源卡上，并标注"巴方称"。
- **两国平民伤亡都要交代**，避免作品只呈现飞机和装备。

## 故事结构

```text
SC00 序：四月 ─┬─ 法拉兹开场 SC01A ─┐
               └─ 罗汉开场 SC01B ───┴─→ SC02 01:05（分屏）
                                          ├─ 跟随法拉兹 SC03A ─┐
                                          └─ 跟随罗汉 SC03B ───┴─→ SC04 黎明与两夜
                                                                    ├─ 法拉兹：5/10 SC05A ─┐
                                                                    └─ 罗汉：5/10 SC05B ───┴─→ SC06 17:00 停火
                                                                                                ├─ 法拉兹结局 SC07A（跟随法拉兹 ≥ 2 次）
                                                                                                └─ 罗汉结局 SC07B（跟随罗汉 ≥ 2 次）
                                                                                                        ↓
                                                                                                片尾来源卡（两个结局共用）
```

三处视角选择各计一次。结局由玩家跟随次数较多的一方决定；三次二选一不会出现平局。两个结局之后都接同一组片尾来源卡。

### 序：四月（约 1 分钟）
标题卡交代帕哈尔加姆遇难人数、外交报复和双方的指控，然后黑屏。玩家选择从谁的那一夜开始。

### 第一章：五月六日深夜（约 2 分钟）
法拉兹在警戒室给妹妹发语音，随后紧急起飞；罗汉在任务简报后和尼尔一起走向飞机。两条线互为镜像，只在玩家选中的一侧展开。

### 第二章：01:05（约 2 分钟，分屏）
两人第一次出现在同一画面里：左边是罗汉的打击航线，右边是法拉兹在爬升中收到的引导指令。玩家选择接下来跟随谁进入空战。

### 第三章：五十二分钟（约 3 分钟）
- **跟随法拉兹：** 引导员给出目标，导弹离架，目标航迹消失。法拉兹报告"航迹丢失"，得到的回答是"无法确认"。
- **跟随罗汉：** 雷达告警、规避，无线电里尼尔的呼号再也没有回答。

### 第四章：黎明与两夜（约 2 分钟）
落地后，法拉兹打给妹妹：她没事，但街那头的清真寺被炸了。罗汉一遍遍拨尼尔的电话，没人接；他再打给母亲，母亲说查谟一切都好。电视上两国的说法互相矛盾。5 月 8–9 日的无人机之夜以蒙太奇呈现，其中查谟的夜空也亮了起来。玩家选择 5 月 10 日凌晨跟随谁。

### 第五章：五月十日（约 2 分钟）
- **跟随法拉兹：** 02:09 起，巴方空军基地接连遭到打击。法拉兹坐在座舱里待命，听着一个个基地的名字从频道里报出来；博拉里有 5 名空军人员死亡。
- **跟随罗汉：** 巴方反击的无人机和导弹飞向印方基地，罗汉和地勤一起躲进掩体。另一座基地传来一名空军士官阵亡的消息。母亲的电话打不通。

### 第六章：17:00（约 1 分钟）
停火。分屏的两半天空慢慢合成一片。两国平民伤亡并列出现，各自注明"据本国政府统计"。

### 结局与片尾来源卡（约 1–2 分钟）
- **法拉兹结局：** 中队被公开记功，法拉兹翻开自己的任务记录："发射 2 枚，结果：未确认。"他坐车去穆扎法拉巴德看妹妹，两人站在被炸的清真寺外。
- **罗汉结局：** 罗汉在军医院找到尼尔。尼尔弹射时受了伤，躺在病床上，还在开玩笑。罗汉把那包糖放在他床头。字幕：5 月 11 日，印度空军称所有飞行员均已回家。
- **片尾来源卡（共用）：** 按时间顺序列出双方的战损声明和独立评估，每张注明发布者、日期和证据状况。最后一张固定为："本作选择不改变历史结果；空战画面为重建演示，不是档案影像。"

## 场景脚本草案

画面中凡属重建演示的镜头，左下角都常驻"重建演示"标签；所有对白都是创作对白。

### SC00 — 序：四月
**画面：** 黑底白字：4 月 22 日、帕哈尔加姆、26 人遇难。随后是条约文本被划线、两国机场的航班牌依次变为"取消"。不出现袭击画面。  
**旁白：** "4 月 22 日，帕哈尔加姆附近的袭击造成 26 名平民遇难。印度指向巴基斯坦，巴基斯坦否认。两周后，两国之间的天空关闭了。"  
**选项：** 从法拉兹的那一夜开始 / 从罗汉的那一夜开始。  
**事实引用：** F01、F02。

### SC01A — 法拉兹：警戒室
**画面：** 明哈斯基地的警戒室，凌晨。法拉兹对着手机录语音："睡吧，我在天上。"警铃响起，他跑向停机坪。一排 J-10C 已经挂好 PL-15，座舱盖依次合上，两架两架地滑出。  
**引导员（无线电，英语）：** "利爪 2，向东爬升。东边的航迹还在增加。"  
**法拉兹（乌尔都语，自语）：** "这不像演习。"  
**旁白字幕：** "据巴方《黎明报》，第 15 中队'眼镜蛇'当晚出动了 20 架 J-10C 中的 18 架。"  
**事实引用：** F07、F08。  
**标注：** 引导员的具体位置（地面站或预警机）不交代，只以无线电声音出现。

### SC01B — 罗汉：简报室
**画面：** 前线基地，深夜。简报结束，尼尔一边戴头盔一边逗罗汉："学长，回来请我吃那包糖。"罗汉没理他。"阵风"机腹下挂着 SCALP 巡航导弹，翼下挂着 HAMMER 炸弹。座舱盖合上，平视显示器亮起。  
**简报官（英语）：** "不越过边境。打完就回。"  
**罗汉（印地语，自语）：** "不过线。打完就回。"  
**旁白字幕：** "据印度媒体援引消息人士，'阵风'当晚挂载了 SCALP 和 HAMMER。"  
**事实引用：** F04。

### SC02 — 01:05（分屏）
**画面：** 左半屏：罗汉的编队在印方领空内爬升，SCALP 脱离挂架，尾焰拖向西方。右半屏：法拉兹的平视显示器上，引导指令把他转向东方。地图角落标出 9 个打击点（示意）。  
**旁白：** "01:05 到 01:30，印度打击了 9 处地点。印方说那里是恐怖组织设施，巴方说那里是平民区和清真寺。"  
**引导员（无线电，英语）：** "所有单位，他们开火了。"  
**选项：** 跟随法拉兹进入空战 / 跟随罗汉进入空战。  
**事实引用：** F03、F04、F05。

### SC03A — 法拉兹：五十二分钟
**画面：** 座舱内，平视显示器上跳出引导员分配的目标，距离数字在缩小。法拉兹按下发射键，机身轻轻一震，导弹尾焰划向东方的黑暗，然后是第二枚。屏幕上，那个目标航迹闪了几下，消失了。  
**法拉兹（英语，无线电）：** "利爪 2，导弹离架。目标航迹丢失。"  
**引导员：** "收到。无法确认。"  
**法拉兹（乌尔都语，低声）：** "航迹丢失，不等于击落。"  
**旁白：** "超过一百架飞机，没有一架越过边境。PL-15 远程导弹第一次在实战中发射。据巴方军官说，交战持续了大约五十二分钟。"  
**事实引用：** F05、F06、F07、F08。  
**标注：** 法拉兹分配到的目标只以雷达航迹符号出现，不显示机型，也不对应任何一处真实坠机。

### SC03B — 罗汉：五十二分钟
**画面：** 返航途中，告警音突然响起，平视显示器上闪出威胁方向。罗汉压杆、抛撒干扰弹，夜空中拉出一串光点。无线电里，尼尔的呼号叫了三遍，没有回答。很远的地面上，有一团火光。  
**罗汉（英语，无线电）：** "游隼 4，报告位置。尼尔？尼尔！"  
**旁白：** "那天凌晨，印度境内至少有三处地方落下了战机残骸。"  
**事实引用：** F05、F07、F10。  
**标注：** 尼尔是虚构人物，他的失联不对应任何一处真实坠机点，也不暗示具体机型。

### SC04 — 黎明与两夜
**画面：** 两人各在自己的基地，天刚亮。  
- 法拉兹拨通萨娜的电话。萨娜的声音在发抖："我没事。街那头的清真寺……被炸了。"电视里，巴方称击落 5 架（以"声明卡"呈现，不用真实录像）。  
- 罗汉一遍遍拨尼尔的号码，没人接。他打给母亲，母亲问他吃饭了没有。电视里，印方不谈损失。手机上，一张田地里的导弹残骸照片在传播。  

随后是 5 月 8–9 日的蒙太奇：城市灯火管制，S-400 夜间发射，巡飞弹和无人机的光点在两国上空交错。查谟的夜空也亮了起来，罗汉在基地里看着新闻，再次拨母亲的电话。  
**旁白：** "第二天起，天空里多了更小、更便宜的东西。印方说 S-400 第一次在实战中开火，巴方说击落了几十架以色列产无人机。双方都否认对方指控的袭击。"  
**选项：** 5 月 10 日凌晨跟随法拉兹 / 跟随罗汉。  
**事实引用：** F03、F09、F10、F11、F12、F15、F23、F24。

### SC05A — 法拉兹：五月十日
**画面：** 02:09，法拉兹坐在座舱里待命，座舱盖开着。频道里传来："努尔汗被击中。"之后，更多基地的名字接连报出。远处的地平线上有火光。镜头切到博拉里：一座机库的屋顶出现一个大洞，里面停着一架"爱立眼"预警机。  
**法拉兹：** "……博拉里？"  
**旁白：** "5 月 10 日凌晨，印度打击了巴方多处空军基地。博拉里的机库里，一架'爱立眼'受损，5 名空军人员死亡。"  
**事实引用：** F16、F17。

### SC05B — 罗汉：五月十日
**画面：** 前线基地警报长鸣，罗汉和地勤一起冲进掩体。夜空中，防空导弹接连升空，低空有无人机的嗡鸣。罗汉拨母亲的电话，一直是忙音。天亮后，跑道边有烧焦的无人机残骸。电台里传来消息：另一座基地，一名空军士官阵亡。母亲终于回了一条短信："我在楼下邻居家，都好。"  
**罗汉：** "他们也来了。"  
**旁白：** "巴方发起反击，称打击了 26 处军事目标。印方承认四处基地受到有限损伤；卫星图未能清楚显示巴方声称的大部分破坏。在查谟一带，炮击又造成了平民死亡。"  
**事实引用：** F18、F22、F24。

### SC06 — 17:00
**画面：** 两边的墙上，时钟同时走到 17:00（巴基斯坦时间 16:30）。法拉兹解开氧气面罩，罗汉放下手机。分屏中间的线慢慢淡去，两半天空合成一片。两国伤亡数字分列左右，各注"据本国政府统计"。  
**旁白：** "停火在下午五点生效。两国平民的死亡人数，比任何一架飞机都更难写进标题。"  
**事实引用：** F19、F20。  
**跳转：** 跟随法拉兹次数多 → SC07A；跟随罗汉次数多 → SC07B。

### SC07A — 法拉兹结局
**画面：** 中队的简报室，电视里正在播报："空军将战果归于第 15 中队。"战友们在鼓掌。法拉兹翻开自己的任务记录，上面写着："发射 2 枚。结果：未确认。"他合上本子。几天后，他在穆扎法拉巴德和萨娜一起站在被炸的清真寺外。萨娜问他："那天晚上，你在天上看见什么了？"法拉兹没有回答。  
**字幕：** "6 月 6 日，巴基斯坦空军将击落战果归于第 15 中队'眼镜蛇'。"  
**事实引用：** F08、F23。随后进入片尾来源卡。

### SC07B — 罗汉结局
**画面：** 军医院的走廊。罗汉推开病房门，尼尔腿上打着石膏，看见他就笑："学长，糖呢？"罗汉把那包一直没拆的糖放在他床头。  
**字幕：** "5 月 11 日，印度空军称：损失是战斗的一部分，所有飞行员均已回家。"  
**事实引用：** F12。随后进入片尾来源卡。

### 片尾来源卡（两个结局共用）
按时间顺序逐张出现，每张注明发布者、日期和证据状况：
1. 5 月 7 日，巴方：击落 5 架印方战机和 1 架无人机（F11）。
2. 5 月 8 日，匿名美国官员对路透社称：高度确信至少 2 架被 J-10 击落（F09）。
3. 5 月 9 日，《华盛顿邮报》：确认 3 处坠机点（F10）。
4. 5 月 28 日，巴方总理：6 架，其中 4 架"阵风"（F11）。
5. 5 月 31 日，印度国防参谋长：承认有损失，否认 6 架之说（F12）。
6. 7 月，法国空天军参谋长：看到 3 架被击落的证据（F13）。
7. 8 月，印度空军参谋长：S-400 击落 5 架巴方战机和 1 架预警机；没有公开证据（F14）。
8. 11 月，美国国会美中经济与安全审查委员会报告：巴方取得军事成功，中国装备首次实战（F21）。

**固定尾卡：** "本作选择不改变历史结果。战果、伤亡数字以来源卡为准；空战画面为重建演示，不是档案影像。"

## 视觉与声音方向

- **两套色调：** 法拉兹一侧是 J-10C 座舱的冷蓝色屏幕光；罗汉一侧是"阵风"座舱的琥珀色仪表光。分屏时左右各用一套，停火时两边合成同一种夜色。
- **两个座舱要能一眼分清：** J-10C 是单块大曲面风挡加气泡座舱盖，"阵风"的座舱盖带前风挡框。两机的平视显示器符号风格也不同，按参考图分别设计，不混用。
- **装备是主角之一：** 所有出现的装备按 [equipment_reference.md](equipment_reference.md) 收集参考图或生成示意图。生成图标注"示意"，不能伪装成新闻照片或档案影像。
- **不越境的空间感：** 用俯视地图交代"两条防线隔着边境"，导弹轨迹在地图上跨越边境，飞机图标始终留在本方一侧。
- **地图：** 用核实过的地理数据制作矢量地图，基地和坠机点的位置按来源标注，不让图像模型生成地理信息。
- **家人线：** 萨娜和罗汉母亲的戏只用电话声音、短信和语音消息来呈现，画面停留在飞行员身上，不拍摄或生成家人在空袭中的画面。
- **声音：** 发动机声、雷达告警音和无线电底噪可以用合成或授权音效。不伪造真实的无线电录音；角色的通话全部标为创作对白。
- **国家符号：** 两国国旗和空军机徽按真实样式绘制，不做丑化或夸张处理。两个角色的戏份和镜头分量保持对等。

## 来源清单

| ID | 来源 | 用于 |
| --- | --- | --- |
| S01 | AP News, "Indian survivors of Kashmir attack say gunmen asked if they were Hindus and opened fire" (2025-04-30) <https://apnews.com/article/kashmir-attack-india-pakistan-victims-a5492962cd86174262cb73b85c04c51a> | F01 |
| S02 | Al Jazeera, "Pakistan claims Pahalgam attack 'false flag operation'" (2025-04-24) <https://www.aljazeera.com/news/liveblog/2025/4/24/kashmir-attack-live-india-summons-pakistani-envoy-hunts-pahalgam-gunmen> | F01 |
| S03 | CNN, Pahalgam explainer (2025-04-24) <https://edition.cnn.com/2025/04/24/india/pahalgam-india-pakistan-attack-explainer-intl-hnk> | F02 |
| S04 | Hindustan Times, "'Act of war': Pakistan closes airspace to Indian airlines" (2025-04-24) <https://www.hindustantimes.com/india-news/act-of-war-pakistan-closes-airspace-to-indian-airlines-suspends-all-trade-101745495389616.html> | F02 |
| S05 | 印度外交部，Operation Sindoor 特别简报（2025-05-07） <https://www.mea.gov.in/media-briefings.htm?dtl/39474/Transcript_of_Special_Briefing_on_OPERATION_SINDOOR_May_07_2025> | F03 |
| S06 | Reuters, "India launches attack on 9 sites in Pakistan…" (2025-05-06) <https://www.reuters.com/world/india/india-launches-attack-9-sites-pakistan-pakistan-occupied-jammu-kashmir-2025-05-06/> | F03 |
| S07 | IISS, "India–Pakistan drone and missile conflict: differing and disputed narratives" (2025-05-15) <https://www.iiss.org/online-analysis/online-analysis/2025/05/indiapakistan-drone-and-missile-conflict-differing-and-disputed-narratives/> | F03 |
| S08 | India Today, "Rafale jets hit Pak terror camps with Scalp missiles, Hammer bombs: Sources" (2025-05-07) <https://www.indiatoday.in/india/story/rafale-jets-pak-terror-camps-operation-sindoor-pahalgam-attack-retaliation-2720674-2025-05-07> | F04 |
| S09 | The Hindu, "Artillery's firepower reverberates during Operation Sindoor" (2025-05-24) <https://www.thehindu.com/news/national/artillerys-firepower-reverberates-during-operation-sindoor/article69615205.ece> | F04 |
| S10 | AirForces Monthly / Key Aero："Understanding the Rafale kills"（2025-10）<https://www.key.aero/article/full-article-understanding-rafale-kills>；"A close call" <https://www.key.aero/article/close-call> | F05 F06 F14 F16 |
| S11 | The Daily Telegraph, "China helped Pakistan shoot down Indian planes, report says" (2025-05-08) <https://www.yahoo.com/news/china-helped-pakistan-shoot-down-142036091.html> | F05 |
| S12 | Reuters, "How Pakistan shot down India's cutting-edge fighter using Chinese gear" (2025-08-02) <https://www.reuters.com/business/aerospace-defense/how-pakistan-shot-down-indias-cutting-edge-fighter-using-chinese-gear-2025-08-02/> | F07；杀伤链与射程分析（待细读核对） |
| S13 | Reuters, "Exclusive: Pakistan's Chinese-made jet brought down two Indian fighter aircraft, US officials say" (2025-05-08) <https://www.reuters.com/world/pakistans-chinese-made-jet-brought-down-two-indian-fighter-aircraft-us-officials-2025-05-08/> | F07 F09 |
| S14 | Dawn, "Air force credits Cobras with 'six IAF kills'" (2025-06-06) <https://www.dawn.com/news/1915722/> | F08 |
| S15 | The Washington Post, "At least two Indian jets appear to have crashed during Pakistan strikes, visuals show" (2025-05-09) <https://www.washingtonpost.com/world/2025/05/09/fighter-jets-india-pakistan-attack/> | F10 |
| S16 | The Indian Express, Bathinda 坠机遇难者家属报道 (2025-07-23) <https://indianexpress.com/article/cities/chandigarh/kin-dalit-man-died-aircraft-crash-bathinda-seek-govt-compensation-10144682/> | F10 |
| S17 | The New York Times, "The Indian Aircraft Pakistan Says It Shot Down" (2025-05-07) <https://www.nytimes.com/2025/05/07/world/asia/india-pakistan-downed-aircraft.html> | F11 |
| S18 | Anadolu Agency, "Pakistan shot down 6 Indian jets, including 4 French-made Rafale…" (2025-05-28) <https://www.aa.com.tr/en/asia-pacific/pakistan-shot-down-6-indian-jets-including-4-french-made-rafale-during-conflict-premier-sharif/3582409> | F11 |
| S19 | Reuters, "Indian air force says losses are part of combat but all pilots back home" (2025-05-11) <https://www.reuters.com/world/asia-pacific/indian-air-force-says-losses-are-part-combat-all-pilots-back-home-2025-05-11/> | F12 |
| S20 | Bloomberg, "India Confirms It Lost Fighter Jets in Recent Pakistan Conflict" (2025-05-31) <https://www.bloomberg.com/news/articles/2025-05-31/india-confirms-it-lost-fighter-jets-in-recent-pakistan-conflict> | F12 |
| S21 | Al Jazeera, "French intelligence claims China trying to foil global sale of Rafale jets" (2025-07-06) <https://www.aljazeera.com/news/2025/7/6/french-intelligence-claims-china-trying-to-foil-global-sale-of-rafale-jets> | F13 |
| S22 | India Today, "IAF's S-400 Sudarshan Chakra…" (2025-05-08) <https://www.indiatoday.in/science/story/operation-sindoor-iafs-s-400-sudarshan-chakra-missile-shield-that-foiled-paks-escalatory-bid-2721572-2025-05-08> | F15 |
| S23 | India Today, "Pak targeted 36 places with 300–400 'Turkish' drones" (2025-05-09) <https://www.indiatoday.in/india/story/pakistan-india-may-8-attack-turkish-drone-used-400-drones-civilian-planes-radar-india-36-drones-operation-sindoor-2722309-2025-05-09> | F15 |
| S24 | Times of Israel, "Pakistan military says it shot down 25 Israeli-made drones launched by India" <https://www.timesofisrael.com/pakistan-military-says-it-shot-down-25-israeli-made-drones-launched-by-india/> | F15 |
| S25 | Reuters, "How India and Pakistan pulled back from the brink with US-brokered ceasefire" (2025-05-14) <https://www.reuters.com/world/asia-pacific/how-india-pakistan-pulled-back-brink-with-us-brokered-ceasefire-2025-05-13/> | F16 |
| S26 | The Washington Post, "Indian strikes on Pakistan damaged six airfields, Post analysis finds" (2025-05-14) <https://www.washingtonpost.com/world/2025/05/14/india-pakistan-strikes-conflict-damage/> | F16 F17 |
| S27 | The Express Tribune, DG ISPR 简报 (2025-05-11) <https://tribune.com.pk/story/2545242/> | F18 |
| S28 | The New York Times, "India and Pakistan Talked Big, but Satellite Imagery Shows Limited Damage" (2025-05-14) <https://www.nytimes.com/interactive/2025/05/14/world/asia/india-pakistan-attack-damage-satellite-images.html> | F18 |
| S29 | Al Jazeera, 停火协议直播页 (2025-05-10) <https://www.aljazeera.com/news/liveblog/2025/5/10/india-pakistan-live-pakistan-airbases-targeted-as-blasts-rock-north-india> | F19 |
| S30 | BBC, "Kashmir: Modi tells Trump India won't accept 'third-party mediation'" (2025-06-18) <https://www.bbc.com/news/articles/c89ew9wde3lo> | F19 |
| S31 | BBC, "India-Pakistan ceasefire appears to hold after accusations of violations" (2025-05-13) <https://www.bbc.com/news/articles/cvg9d913v20o> | F20 |
| S32 | The Express Tribune, "Number of personnel martyred … rises to 13: ISPR" (2025-05-14) <https://tribune.com.pk/story/2545851/toll-of-personnel-martyred-in-indian-aggression-rises-to-13-ispr> | F20 |
| S33 | U.S.-China Economic and Security Review Commission, 2025 Annual Report to Congress (2025-11-18) <https://www.uscc.gov/sites/default/files/2025-11/2025_Annual_Report_to_Congress.pdf> | F21 |

**来源采集说明：** 本稿的来源线索取自英文维基百科条目"2025 India–Pakistan conflict"（2026-11-01 读取）的引用列表。上表各条目尚未逐篇打开原文核对措辞，进入正式剧本前需要逐条核读，尤其是 S10、S12（付费或长文分析）。

## 待人工确认

- 法拉兹所在的第 15 中队有真实番号（来源 S14），角色本身是虚构的。如果不希望虚构人物挂靠真实部队，可以改为"某 J-10C 中队"。
- 两名角色、萨娜、尼尔的姓名上线前需检索，确认不与已公开的真实参战人员或遇难者重名。
- 是否请熟悉南亚事务、能读乌尔都语和印地语的审阅者检查对白、称谓和地名，尤其是 F03、F23 中目标性质的表述，以及克什米尔地区"印控/巴控"的标注方式。
- S12（路透社 8 月长文）关于 PL-15 射程情报误判的细节，读原文后再决定是否写进 SC03A 的旁白。
- 新闻照片（残骸、卫星图）的使用授权；默认只作为美术参考，不直接进入成片。
