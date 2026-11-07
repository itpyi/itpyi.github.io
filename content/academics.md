---
title: {zh: 学术, en: Academics}
meta:
  zh: 王逸飞的正式履历页，包含研究、教育列表与开源项目。
  en: Formal curriculum vitae of Wang Yifei, including research, education, and open-source work.
subnav: {zh: 学术, en: Academics}
scripts: [assets/js/publications.js]
section-class: cv-section
---
<!-- section {title: {zh: 研究, en: Research}} -->
<!-- lang:zh -->

追溯我的既往研究，可以看出两条主线。一是魔态的容错制备，二是纠错码的代数结构。第一条更贴合我持之以恒的志趣：制造出真正的容错量子计算机；第二条则可看作数学这一业余爱好的副产品。

第一条主线肇端于博士生涯早期。我开始接触量子纠错时，适逢原子阵列的实验突破。因此第一个工作即关注硬件和已有魔态方案的匹配。次年，注意到码手术（code surgery）技术的进展，我立刻意识到它将解放魔态资源制备和储存的形态，遂对此做了分析。分析此想法时，我曾采用 Stim 做数值模拟，以 S 门替代 T 门，但终不觉此模拟方法真正可靠。彼时直觉相信魔态方案不难模拟，因其所涉魔态资源仅限于其逻辑自由度，但因工程规模似远超我的执行力而未能实施。今年九月，人工智能技术突飞猛进，我终于在其帮助下落实了直觉，做出了支持真实含 T 线路的高效模拟器 [magna](https://github.com/itpyi/magna)。

第二条主线起源于和同行的讨论。起初，与合作者完成了一项关于双变量双循环码中拓扑纠缠熵的工作，由此我偶然获知二维拓扑码和环面码的关系，并很快意识到其解耦问题不能由简单的高斯消元解决。依靠与合作者密切而及时的讨论，我们找到了合适的同调代数工具，解决了这一问题。与此相关的后续研究我仍在持续参与，而同调代数、代数几何、K 理论等仍然是我长期的业余爱好。

当前，我的主要兴趣仍继承第一条主线，在于魔态制备。具体来说，包括提出新的实用方案、分析魔态制备的线路结构、开发更高效的模拟器等。除此之外，将原子平台中的真实约束和真实错误模型更完整地考虑进容错方案、量子计算机的容错互联、人工智能参与的大规模自动化设计等，也是我近期和未来关心且希望尝试的问题。

<!-- lang:en -->
Looking back over my research, I see two main threads. One is the fault-tolerant preparation of magic states; the other is the algebraic structure of quantum error-correcting codes. The first is closer to my enduring ambition: to build a working fault-tolerant quantum computer. The second might be seen as a by-product of my pursuit of mathematics as a hobby.

The first thread began early in my PhD. My introduction to quantum error correction coincided with experimental breakthroughs in neutral-atom arrays. My first project therefore focused on matching existing magic-state protocols to the hardware. The following year, I noticed advances in code surgery and immediately recognised that they could free us from existing constraints on how magic-state resources are prepared and stored. I set out to analyse these possibilities. In doing so, I used Stim for numerical simulations, substituting S gates for T gates, but never felt fully confident in the reliability of this approach. Even then, my intuition was that magic-state protocols should be tractable to simulate, since the magic resources they involve are confined to their logical degrees of freedom. Yet the software engineering effort seemed far beyond what I could manage, and I left the idea unrealised. This September, with AI advancing rapidly, I finally put that intuition into practice with its help, building [magna](https://github.com/itpyi/magna), an efficient simulator that supports circuits with actual T gates.

The second thread grew out of discussions with colleagues. It began with a joint study of topological entanglement entropy in bivariate bicycle codes. Through this work, I happened to learn about the relationship between two-dimensional topological codes and toric codes, and soon realised that the associated decoupling problem could not be solved by straightforward Gaussian elimination. Through close and timely discussions with my collaborators, we found the right tools from homological algebra and solved the problem. I continue to take part in related follow-up work, while homological algebra, algebraic geometry and K-theory remain long-standing interests that I pursue as a hobby.

My main interests today still follow the first thread: magic-state preparation. Specifically, I am interested in devising new practical protocols, analysing the circuit structure of magic-state preparation, and developing more efficient simulators. Beyond this, I would like to explore how to incorporate realistic constraints and noise models of neutral-atom platforms more fully into fault-tolerant protocols, how to interconnect quantum computers fault-tolerantly, and how AI can assist in large-scale automated design. These are questions I hope to pursue in the near term and beyond.

<!-- section {title: {zh: 相关链接, en: Links}} -->
<!-- lang:zh -->
- [ORCID](https://orcid.org/0009-0003-1126-1628)
- [SciRate](https://scirate.com/wang-yifei)
- [Google Scholar](https://scholar.google.com/citations?user=dwTYUPwAAAAJ)
- [Stack Exchange](https://stackexchange.com/users/17951034/itpyi)

<!-- lang:en -->
- [ORCID](https://orcid.org/0009-0003-1126-1628)
- [SciRate](https://scirate.com/wang-yifei)
- [Google Scholar](https://scholar.google.com/citations?user=dwTYUPwAAAAJ)
- [Stack Exchange](https://stackexchange.com/users/17951034/itpyi)

<!-- section {kind: publications, title: {zh: 学术论文, en: Publications}, id: publication} -->

<!-- section {layout: cards, title: {zh: 开源, en: Open Source}} -->
<!-- lang:zh -->
详见[开源项目](opensource.html)。

### magna — 魔态工厂模拟器

通过全局张量网络收缩评估魔态工厂的接受率与输出态保真度，支持非 Clifford 门、Pauli 噪声及依赖解码器输出的经典前馈。

对应论文：[arXiv:2610.22315](https://arxiv.org/abs/2610.22315)

- [GitHub Repo](https://github.com/itpyi/magna)
- [使用文档](https://itpyi.github.io/magna/)

### AtomISA — AOD 原子运动可视化

基于浏览器的交互式模拟器，用于 AOD 原子运动（AAM）模型——中性原子量子计算平台中的原子重排过程。纯 HTML + JavaScript，无需依赖。

- [GitHub Repo](https://github.com/itpyi/AtomISA)
- [在线演示](https://itpyi.github.io/AtomISA)

### surface_magic

基于格手术的门传输模拟，包含线路级噪声模拟与态矢量分析。

对应论文：[arXiv:2503.19758](https://arxiv.org/abs/2503.19758)

- [GitHub Repo](https://github.com/itpyi/surface_magic)

### error_msd

物理层魔态提纯态矢量模拟。

对应论文：[arXiv:2312.09111](https://arxiv.org/abs/2312.09111)

- [GitHub Repo](https://github.com/itpyi/error_msd)

### Typst templates and packages

包括 hetvid、ega-numbering、fig-plucker 等模板与包。

- [hetvid](https://github.com/itpyi/hetvid)
- [ega-numbering](https://github.com/itpyi/typst-ega-numbering)
- [fig-plucker](https://github.com/itpyi/typst-plot)

<!-- lang:en -->
See [open source projects](opensource.html) for details.

### magna — Magic State Factory Simulator

Evaluates acceptance rates and output-state fidelities of magic state factories through global tensor-network contraction, supporting non-Clifford gates, Pauli noise, and classical feedforward conditioned on decoder outputs.

Related paper: [arXiv:2610.22315](https://arxiv.org/abs/2610.22315)

- [GitHub Repo](https://github.com/itpyi/magna)
- [Documentation](https://itpyi.github.io/magna/)

### AtomISA — AOD Atom Motion Visualization

Interactive browser-based simulator for AOD Atom Motion (AAM), a model of atom rearrangement in neutral-atom quantum computing platforms. Visualises pickup, motion, and offload phases with real-time canvas animation. Pure HTML + JavaScript, no dependencies.

- [GitHub Repo](https://github.com/itpyi/AtomISA)
- [Live Demo](https://itpyi.github.io/AtomISA)

### surface_magic

Simulation of surgery-based gate teleportation, including circuit-level noise simulation and state-vector analysis.

Related paper: [arXiv:2503.19758](https://arxiv.org/abs/2503.19758)

- [GitHub Repo](https://github.com/itpyi/surface_magic)

### error_msd

State-vector simulation for physical-level magic state distillation.

Related paper: [arXiv:2312.09111](https://arxiv.org/abs/2312.09111)

- [GitHub Repo](https://github.com/itpyi/error_msd)

### Typst templates and packages

Includes hetvid, ega-numbering, fig-plucker, and related writing/plotting tools.

- [hetvid](https://github.com/itpyi/hetvid)
- [ega-numbering](https://github.com/itpyi/typst-ega-numbering)
- [fig-plucker](https://github.com/itpyi/typst-plot)

<!-- section {layout: timeline, title: {zh: 教育, en: Education}} -->
<!-- lang:zh -->
### 2022 – 至今

#### 清华大学杨振宁高等研究院

理论物理学博士研究生

研究方向：容错量子计算

### 2018 – 2022

#### 北京大学物理学院

物理学学士

毕业论文：[格点规范理论的量子模拟](assets/docs/2022_Peking_University_Undergraduate_Thesis.pdf)

### 2012 – 2018

#### 陕西师范大学附属中学

初中和高中

### 2006 – 2012

#### 西安市临潼区陕缝学校

小学

<!-- lang:en -->
### 2022 – Now

#### Chen-Ning Yang Institute for Advanced Study, Tsinghua University

PhD candidate in theoretical physics

Research fields: fault-tolerant quantum computation

### 2018 – 2022

#### School of Physics, Peking University

Bachelor in physics

Thesis: [Quantum Simulation of Lattice Gauge Theory (in Chinese)](assets/docs/2022_Peking_University_Undergraduate_Thesis.pdf)

### 2012 – 2018

#### The High School Affiliated to Shaanxi Normal University

Junior and senior high school

### 2006 – 2012

#### Shaanfeng School, Lintong District, Xi'an

Primary school, now demolished
