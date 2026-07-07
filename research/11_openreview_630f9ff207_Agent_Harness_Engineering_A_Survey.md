|     | Agent |        | Harness  |             | Engineering: |         |           | A     | Survey  |     |
| --- | ----- | ------ | -------- | ----------- | ------------ | ------- | --------- | ----- | ------- | --- |
|     |       | Junjie | Li1,6,*, | Xi Xiao6,*, |              | Yunbei  | Zhang5,*, | Chen  | Liu2,*, |     |
|     |       | Zhao4, |          |             | Liao3,       |         | Ji6,      |       | Wang6,  |     |
|     |       | Lin    |          | Xiaoying    |              | Yingrui |           | Janet |         |     |
Jianyang Gu7, Yingqiang Ge9, Weijie Xu9, Xi Fang9, Xiang Xu9,
| Tianchen |       | Zhao9,         |     | Youngeun | Kim9, | Tianyang |         | Wang6, | Jihun      | Hamm5, |
| -------- | ----- | -------------- | --- | -------- | ----- | -------- | ------- | ------ | ---------- | ------ |
|          | Smita | Krishnaswamy2, |     |          | Jun   | Huan9,   | Chandan |        | K Reddy8,9 |        |
1CMU, 2Yale, 3JHU, 4NEU, 5Tulane, 6UAB, 7OSU, 8Virginia 9Amazon
Tech,
|     |     |     |     | Project | Page: Awesome-Agent-Harness |     |     |     |     |     |
| --- | --- | --- | --- | ------- | --------------------------- | --- | --- | --- | --- | --- |
Abstract
The rapid deployment of large language model (LLM) agents in production has revealed
a recurring pattern: task execution reliability depends less on the underlying model
than on the infrastructure layer that wraps it, the agent execution harness. This sur-
vey provides a practice-grounded, systematic treatment of agent harness engineering,
organized around three claims. First, the agent harness is an independent system layer
whose engineering quality drives a large share of real-world reliability, a position we
develop through a three-phase engineering evolution from prompt to context to har-
ness engineering, a cross-layer synthesis covering the cost–quality–speed trilemma, the
capability–control tradeoff, and the harness coupling problem, and an open-problem
agenda grounded in both research gaps and production pain points. Second, we propose
ETCLOVG, a seven-layer taxonomy (Execution environment, Tool interface, Context
management, Lifecycle/Orchestration, Observability, Verification, Governance) that ex-
tends prior six-component frameworks by treating observability and governance as in-
dependent architectural concerns. Third, we map 170+ open-source projects onto this
taxonomy to expose ecosystem patterns, coverage gaps, and emerging design princi-
ples, alongside engineering principles distilled from production deployments at OpenAI,
Anthropic, and LangChain that address the gap between practitioner knowledge and
| research |        | vocabulary. |         |            |            |         |     |         |              |     |
| -------- | ------ | ----------- | ------- | ---------- | ---------- | ------- | --- | ------- | ------------ | --- |
|          | Figure | 1:          | A brief | comparison | of prompt, | context | and | harness | engineering. |     |
1

Under review as submission to TMLR
Contents
1 Introduction 4
1.1 The Binding Constraint: Harness over Model . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
1.2 The Practitioner–Research Gap . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
1.3 Scope and Contributions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
2 Background and Taxonomy 5
2.1 Evolution of Agent Systems . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
2.2 Three Engineering Phases . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
2.3 The ETCLOVG Seven-Layer Taxonomy . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
2.4 Scope . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.5 Project Collection Procedure . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
2.6 Inclusion and Exclusion Criteria . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
2.7 Coding Protocol . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
2.8 Limitations of the Corpus . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
2.9 Aggregate Analysis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 10
3 Execution Environment and Sandbox (E) 11
3.1 Scope and Concepts . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
3.2 Categories of Agent Sandboxes . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
3.3 Threat Model and Sandbox Escape . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
3.4 Deployment Modes . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 15
3.5 Summary . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
4 Tool Interface and Protocol Layer (T) 16
4.1 Protocol and Interface Standards . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
4.2 Tool Description, Discovery, and Selection . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
4.3 Tool-Augmented Training and Integration . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
4.4 Scalability and Session Management . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
5 Context and Memory Management (C) 18
5.1 Why Context Must Be Engineered . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 19
5.2 From Prompt Engineering to Context Engineering . . . . . . . . . . . . . . . . . . . . . . . . 20
5.3 Short-Term: Managing the Active Context Window . . . . . . . . . . . . . . . . . . . . . . . 20
5.4 Mid-Term: Session State and Cross-Run Persistence . . . . . . . . . . . . . . . . . . . . . . . 21
5.5 Long-Term: Persistent Memory Systems . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
5.6 Long-Horizon Techniques: Keeping Agents Coherent Over 100+ Turns . . . . . . . . . . . . . 24
5.7 Context Drift and the Limits of Current Approaches . . . . . . . . . . . . . . . . . . . . . . . 24
6 Lifecycle and Orchestration (L) 25
6.1 Lifecycle State Management . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 26
6.2 Single-Agent Inner Loop . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
6.3 Multi-Agent Orchestration Patterns . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
6.4 Full Lifecycle Pipeline from Issue to Pull Request . . . . . . . . . . . . . . . . . . . . . . . . . 27
2

| Under review    | as  | submission | to         | TMLR |     |
| --------------- | --- | ---------- | ---------- | ---- | --- |
| 7 Observability |     | and        | Operations | (O)  | 28  |
7.1 Tracing and Monitoring Platforms . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
7.2 Agent-Specific Operations Platforms . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 29
7.3 Cost Tracking and Optimization . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 30
7.4 Reliability Engineering . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 30
7.5 Discussion: Toward Unified Observability . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 31
| 8 Verification |     | and Evaluation |     | (V) | 32  |
| -------------- | --- | -------------- | --- | --- | --- |
8.1 Harness Evaluation as a Task-to-Feedback Lifecycle. . . . . . . . . . . . . . . . . . . . . . . . 32
8.2 Stage 1: Task and Benchmark Grounding . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 33
8.3 Stage 2: Pre-execution Readiness Validation . . . . . . . . . . . . . . . . . . . . . . . . . . . . 34
8.4 Stage 3: Controlled Execution and Trace Capture. . . . . . . . . . . . . . . . . . . . . . . . . 35
8.5 Stage 4: Multi-level Judgement and Failure Attribution . . . . . . . . . . . . . . . . . . . . . 36
8.6 Stage 5: Continuous Regression and Deployment Feedback. . . . . . . . . . . . . . . . . . . . 38
8.7 Summary . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 39
| 9 Governance |     | and Security |     | (G) | 39  |
| ------------ | --- | ------------ | --- | --- | --- |
9.1 Permission Models and Identity Management . . . . . . . . . . . . . . . . . . . . . . . . . . . 39
9.2 Lifecycle Hooks . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41
9.3 Component Hardening . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 42
9.4 Declarative Constitutions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 43
9.5 Audit Infrastructure . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 44
9.6 Situating Governance in the Agent Security Landscape . . . . . . . . . . . . . . . . . . . . . . 45
9.7 Research Directions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 46
| 10 Cross-Cutting |     | Concerns  |     |     | 47  |
| ---------------- | --- | --------- | --- | --- | --- |
| 11 Cross-Layer   |     | Synthesis |     |     | 48  |
11.1 Cost-Quality-Speed Trilemma . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
11.2 Capability-Control Tradeoff . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
11.3 Harness Coupling Problem. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
11.4 From Agent Frameworks to Agent Platforms . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
11.5 Open Research Agenda . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 49
| 12 Open | Problems | and | Future | Directions | 49  |
| ------- | -------- | --- | ------ | ---------- | --- |
12.1 Hardening and Scaling Execution Environments . . . . . . . . . . . . . . . . . . . . . . . . . . 49
12.2 Maintaining Reliable State in Long-Running Agents . . . . . . . . . . . . . . . . . . . . . . . 49
12.3 Diagnosing Failures from Agent Traces . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 50
12.4 Standard Handoffs Across Agents, Tools, and Humans . . . . . . . . . . . . . . . . . . . . . . 50
12.5 Keeping Harnesses Useful as Models Improve . . . . . . . . . . . . . . . . . . . . . . . . . . . 51
| 13 Conclusion |     |     |     |     | 51  |
| ------------- | --- | --- | --- | --- | --- |
3

Under review as submission to TMLR
1 Introduction
1.1 The Binding Constraint: Harness over Model
The academic study of LLM-based agents has, by and large, been a study of the model. Research agendas
center on what the model can do: whether it can plan across multiple steps, call tools reliably, retrieve
and compress relevant memories, or coordinate with other agents. The implicit assumption is that agent
capability is primarily a function of model capability, that a sufficiently capable model with a sufficiently
good prompt will produce sufficiently reliable behavior.
Recent empirical evidence challenges the assumption that better models alone produce more reliable agents.
Threerecentresultsestablishthepattern. Bölük(2026a)modifiedonlytheedit-toolformatandsurrounding
tool harness, with no model modification, and reported gains of up to 10× on coding benchmarks across 15
models. Trivedy(2026)improvedafixedGPT-5.2-Codexagentfrom52.8%to66.5%onTerminal-Bench2.0
throughsystempromptrestructuring, middlewarecontextinjection, andself-verificationhooksalone, a13.7
percentage point gain achieved entirely through infrastructure changes. Meta-Harness (Lee et al., 2026)
achieved 76.4% on Terminal-Bench-2 via automated harness optimization, surpassing all hand-engineered
approaches without modifying model weights. In each case, the variable was the execution harness (the
infrastructure layer governing context construction, tool interaction, orchestration, feedback, and execution
constraints);themodelwasheldfixed. Eachoftheseharness-onlygainsexceedsthetypical2to4percentage
point improvements reported as meaningful model advances on the same benchmarks. The pattern is not
incidental: the harness, not the model, is driving the outcome.
We refer to this pattern as the binding-constraint thesis (Bölük, 2026b): for long-horizon tasks evaluated
across comparable frontier models, benchmark variance may be driven as much by the execution harness as
by the model itself. We use this thesis as the framing for the remainder of the survey.
Figure 3 in §2 illustrates the same shift historically: early systems concentrated capability in a single model
loop, whereas later systems increasingly expose reliability as a cross-layer infrastructure problem.
1.2 The Practitioner–Research Gap
A tension exists between practitioner urgency and research vocabulary. OpenAI explicitly framed “harness
engineering” as the discipline of designing environments, constraints, documentation, and feedback loops
aroundCodexagents,reportinginFebruary2026thatasmallteamproducedaninternalproductofroughly
one million lines over five months without manually writing production code (OpenAI, 2026a). Anthropic’s
agent-engineering posts arrived at the same principle from adjacent directions: effective agents should use
simpleandinspectablearchitectures,toolinterfacesshouldbedesignedforagentuseratherthancopiedfrom
human-facing APIs, context should be progressively disclosed instead of eagerly loaded, and long-running
work requires durable handoff artifacts and recoverable execution infrastructure (Anthropic, 2024a; Aizawa,
2025; Anthropic Applied AI Team, 2025; Anthropic, 2025d; 2026b). An article on Martin Fowler’s site
characterizes harness engineering as “cybernetic governors for AI agents,” consisting of feedforward guides
and feedback sensors that form control loops around LLMs (Böckeler, 2026).
The research community, meanwhile, has been studying the components of agent systems with increasing
precision: memory, tool use, planning, and safety. What has not been studied systematically is the system
that integrates these components into reliable operation. The result is a practitioner–research gap: practi-
tioners know that harness infrastructure matters but lack the formal vocabulary to describe why, in terms
that enable systematic improvement. This survey attempts to bridge that gap.
1.3 Scope and Contributions
This survey focuses on the infrastructure layer that wraps a language model to manage long-running, multi-
step task execution. We do not survey agent frameworks as development tools, agent platforms as product
categories, or model capabilities per se, though all three inform our analysis. Figure 4 summarizes the
seven-layer taxonomy that structures the remainder of the survey.
4

Under review as submission to TMLR
Our contributions are organized around three claims.
1. Claim 1 (Conceptual): Building on the binding-constraint thesis (Bölük, 2026b), we
argue that the harness, not the model alone, is the binding constraint on real-world
agentreliability. Threerecentresultsshowharness-onlygainsofupto10×oncodingbenchmarks,
+13.7percentagepointsonTerminal-Bench2.0,and76.4%onTerminal-Bench-2(§1),eachexceeding
typical model-driven gains on the same benchmarks. We develop this thesis through a three-phase
engineering evolution (§2), a cross-layer synthesis covering the cost–quality–speed trilemma, the
capability–control tradeoff, and the harness coupling problem (§11), and an open-problem agenda
(§12).
2. Claim 2 (Classificatory): The seven-layer ETCLOVG taxonomy treats Observability
and Governance as first-class layers rather than side effects of lifecycle hooks. Each has
itsownproductiontoolingstack(LangfuseandOpenTelemetryontheobservabilityside;permission
engines, gateways, and audit pipelines on the governance side) and is owned by a different team in
productiondeployments. WealsoplacestatemanagementinsideLifecycleandOrchestration,where
state lives next to the execution flow that reads and writes it (§2.3).
3. Claim3(Empirical): Mapping170+open-sourceprojectsontoETCLOVGshowswhere
the ecosystem is dense, where it is thin, and which categories earlier corpora missed.
Themappingisthelargestopen-sourceagent-harnesscorpustodate. Execution,Tooling,Lifecycle,
and Verification are densely covered; Observability and Governance are thinner and more often live
in commercial platforms; and three categories absent from earlier corpora, including task runners,
multi-agent orchestrators, and spec-driven development tools, are now first-class. The methodology
subsections (§2.4–§2.9, Appendix A) make the coding reproducible, and the mapping supports the
layer-by-layer observations in §3–§9.
2 Background and Taxonomy
2.1 Evolution of Agent Systems
The trajectory from early chain-of-thought prompting to autonomous agents can be understood as a pro-
gressive expansion of the engineering surface that practitioners must manage.
The ReAct era (2022–2023). Yao et al. (2023) established the observe-think-act loop as a foundational
primitive. Early systems operated with minimal infrastructure: a while-loop, a prompt template, and a
small tool dispatch table. AutoGPT and BabyAGI showed the ambition of fully autonomous operation by
wrappinglanguage-modelcallswithtaskqueues,memory,andtooldispatch,whilealsomakingfailuremodes
suchasexecutionrunaway,contextblowout,stateloss,andunmonitoredsideeffectsvisibleasinfrastructure
problems rather than prompt-only problems (Significant Gravitas, 2023; Nakajima, 2023).
Tool integration and multi-agent coordination (2023–2024). Gorilla, ToolLLM, and Toolformer
establishedthattool-usecapabilitycanbelearnedorinducedratherthanhard-codedintoafixedAPIwrap-
per (Patil et al., 2024b; Qin et al., 2024; Schick et al., 2023). CAMEL, ChatDev, MetaGPT, and Mixture-
of-Agents introduced multi-agent coordination patterns, ranging from role-playing dialogue to software-
development organizations and layered agent aggregation (Li et al., 2023a; Qian et al., 2023a; Hong et al.,
2023; Wang et al., 2024). Evaluation infrastructure matured with SWE-bench, AgentBench, WebArena,
and GAIA (Jimenez et al., 2024; Liu et al., 2023a; Zhou et al., 2024; Mialon et al., 2023), while protocol
standardizationbeganwithAnthropic’sMCPandGoogle’sA2A(Anthropic,2024c;Surapanenietal.,2025).
Theharnessturn(2025–2026). By2025,enoughdeploymentexperiencehadaccumulatedtomakeaclear
case that the binding constraint on agent reliability was infrastructure quality rather than model quality.
Three independent developments in early 2026 validated this shift: OpenAI’s explicit adoption of “harness
engineering” as a discipline, Stanford/MIT’s Meta-Harness showing that automated harness optimization
surpasses hand engineering, and LangChain’s DeepAgents improving from 52.8% to 66.5% on Terminal-
5

Under review as submission to TMLR
Bench 2.0, corresponding to a 13.7 percentage point gain and roughly 26% relative improvement, through
harness layer changes alone (OpenAI, 2026a; Lee et al., 2026; Trivedy, 2026).
2.2 Three Engineering Phases
The 2022–2026 period reveals a coherent three-phase evolution in what the field has chosen to engineer.
Promptengineering(2022–2024). Theprimaryleverwastheinputprompttext. Practitionersoptimized
by crafting better instructions, few-shot examples, and reasoning templates. The engineering scope was
narrow: optimize a single text input to a single model call.
Contextengineering(2025). Asagentsbecamelonger-running,thebindingconstraintshiftedfrom“what
is the input?” to “what information should the model see at each step?” This phase focused on context
management: what to inject on each turn, how to retrieve and compress memories, how to rank tool results
by relevance, and how to handle context window saturation. The scope expanded from a single input to
managingmultipleinformationstreamsflowingintothecontextwindow(AnthropicAppliedAITeam,2025).
Harness engineering (2026). As models became capable enough to handle long-running tasks, reliability
increasingly depended on the infrastructure wrapper that maintains state, mediates tools, injects feedback,
enforces constraints, and verifies progress. This observation aligns with the binding-constraint view that
long-horizon agent performance is produced by a coupled model–harness system rather than by the model
alone (Bölük, 2026b). Harness engineering therefore asks what governance, constraints, feedback loops, and
executioncontrolsmustbedesignedaroundthemodeltomakeagentsystemsreliable. Inourtaxonomy,this
phasetreatsallsevenETCLOVGlayersasanintegratedwhole(OpenAI,2026a;Böckeler,2026;LangChain,
2026b).
Eachphasesubsumestheprevious: harnessengineeringincludescontextengineering,whichincludesprompt
engineering. Thethreephasesalsooverlapintimeandinconceptratherthansucceedingoneanotherbyclean
boundaries. Prompt engineering remains an active part of harness practice today, and context engineering
Figure 2: Illustration of the taxonomy of harness engineering for LLM-based agent systems. The four layers
E, T, C, and L form the structural pillars of the system. The O layer provides system-wide monitoring,
while the V layer delivers evaluation and feedback across components. The G layer enforces governance
and security constraints over the entire system. The color scheme corresponds to the ETCLOVG layers
developed in §2.3.
6

Under review as submission to TMLR
Figure 3: Timeline of representative agent-harness systems from 2022 to 2026. The timeline situates the
shift from early single-loop agents to richer harness infrastructure spanning execution environments, tool
interfaces, context and memory management, lifecycle orchestration, observability, verification, and gover-
nance. The color scheme corresponds to the ETCLOVG layers developed in §2.3.
continuestomatureinparallelwiththeharness-levelconcernswesurveyhere. Ourperiodizationistherefore
best read as a shift in where the marginal engineering effort goes, not as a sequence of replacements.
2.3 The ETCLOVG Seven-Layer Taxonomy
We propose a seven-layer taxonomy for agent harness engineering. We refer to it by the acronym ET-
CLOVG, which stands for Execution, Tooling, Context, Lifecycle, Observability, Verification, Governance.
Figure 4 gives the compact visual map; this subsection fixes the interpretation used throughout the survey.
The first four layers describe the structural core of a harness. Execution (E) determines where agent code
runs and what sandbox constraints bound it; Tooling (T) specifies how external capabilities are described,
discovered, and invoked; Context (C) controls what the model can see over short-term, session-level, and
persistent horizons; and Lifecycle (L) organizes the control flow that reads and writes that state, from
single-agent loops to multi-agent and issue-to-pull-request workflows. The remaining three layers describe
thecontrolplanearoundthatcore. Observability(O)capturestraces,costs,failures,andreliabilitysignals;
Verification (V) turns tasks and traces into evaluation, failure attribution, and regression feedback; and
Governance (G) constrains behavior through permission, identity, policy, hardening, audit, and human
oversight mechanisms. Sections 3–9 develop these seven layers in order, while Sections 10–12 synthesize the
cross-layer tradeoffs and open problems that do not belong to any single layer.
Two design choices distinguish this taxonomy. First, we promote Observability (O) to an independent
layer rather than treating it as a side effect of lifecycle hooks. In production systems, observability has a
dedicated tooling ecosystem (Langfuse, Arize Phoenix, OpenLLMetry) and distinct engineering practices
(OpenTelemetryinstrumentation,costattribution,anomalydetection)thatwarrantindependenttreatment.
Second, we introduce Governance (G) as a first-class layer that captures the full spectrum of security and
7

Under review as submission to TMLR
ssenraHtnegA gnireenignE
General-PurposeManagedSandboxes
Computer-UseAgentInfrastructure
Code-SpecializedSandboxes
ExecutionEnvironment
Framework-IntegratedRuntimes
&Sandbox(E)(§3)
BrowserEvaluationEnvironments
OS-LevelPermissionSandboxes
SandboxAbstractionLayers
ProtocolandInterfaceStandards
ToolDescription,Discovery,andSelection
ToolInterface
&Protocol(T)(§4)
Tool-AugmentedTrainingandIntegration
ScalabilityandSessionManagement
Short-TermActiveContextWindow
Mid-TermSessionStateandCross-RunPersistence
Context&Memory
Long-TermPersistentMemorySystems
Management(C)(§5)
Long-HorizonContextTechniques
ContextDriftandLimits
Single-AgentInnerLoop
Lifecycle&
Multi-AgentOrchestrationPatterns
Orchestration(L)(§6)
FullLifecycleTaskPipelines
TracingandMonitoringPlatforms
Agent-SpecificOperationsPlatforms
Observability&
CostTrackingandOptimization
Operations(O)(§7)
ReliabilityEngineering
UnifiedObservability
TaskandBenchmarkGrounding
Pre-ExecutionReadinessValidation
Verification&
ControlledExecutionandTraceCapture
Evaluation(V)(§8)
Multi-LevelJudgementandFailureAttribution
ContinuousRegressionandDeploymentFeedback
PermissionModelsandIdentityManagement
LifecycleHooks
ComponentHardening
Governance&
Security(G)(§9)
DeclarativeConstitutions
AuditInfrastructure
AgentSecurityLandscape
Figure 4: Details of the agent harness engineering taxonomy. Each branch corresponds to one ETCLOVG
layer and its major subcategories; representative systems and papers are discussed in later sections.
complianceconcernsacrossthreesub-layers: model-level(guardrails,contentfilters),system-level(gateways,
proxies, permission models), and organizational-level (audit, compliance, human-in-the-loop oversight).
8

Under review as submission to TMLR
State management belongs naturally inside Lifecycle and Orchestration (L), alongside the execution flow
that reads and writes it; lifecycle hooks and policy enforcement belong inside Governance (G), where they
align with other constraint mechanisms.
2.4 Scope
Weuseagent harness inanarrowersensethan“anysoftwarearoundanLLM”:theharnessistheengineered
wrapper that turns model calls into bounded, stateful, tool-mediated task execution through execution
substrates, toolinterfaces, contextcontrol, orchestration, observability, evaluationfeedback, andgovernance
constraints (OpenAI, 2026a; Anthropic, 2025d; LangChain, 2026b). The unit of analysis is therefore the
infrastructure that makes long-running agent behavior controllable, inspectable, and recoverable, not the
foundation model or prompt alone. We draw the boundary functionally rather than by product category:
an agent framework is in scope when it exposes reusable mechanisms such as stateful orchestration, tool
routing, runtime policy hooks, or trace capture; a thin model API wrapper, prompt library, static dataset,
generic container runtime, vector database, APM dashboard, or content filter is out of scope unless it is
explicitly adapted to agent execution, state, evaluation, or tool-use governance.
2.5 Project Collection Procedure
Weconstructedthecorpusasasystematicmappingofpubliclydocumentedagent-harnessartifacts,usingthe
reporting discipline of systematic reviews to make the source streams, search strategy, and selection process
explicit (Page et al., 2021). As summarized in Figure 5, candidates were collected from four streams: prior
surveysandbenchmarkpapers,reproducibleGitHubsearchesovernames,descriptions,READMEtext,top-
ics,stars,recency,andarchivalstatus,curatedprojectlistsandpackageregistries,andcompanyengineering
blogs or release notes that introduced harness-level mechanisms (Meng et al., 2026; Jimenez et al., 2024;
Liu et al., 2023a; Zhou et al., 2024; GitHub, 2026; OpenAI, 2026a; Anthropic, 2025d; LangChain, 2026b).
Representative queries combined terms such as agent harness, coding agent, LLM agent sandbox, MCP
server, agent observability, agent memory, agent evaluation, and agent governance. For each re-
tained candidate, we recorded the project name, URL, artifact type, source type, availability status, release
year when identifiable, GitHub metadata when available, and the public evidence used for later ETCLOVG
coding; the metadata snapshot reported in this version was frozen on May 08, 2026.
Figure 5: Corpus construction protocol. Candidate artifacts are gathered from GitHub, papers, curated
lists, package registries, and company engineering sources, then deduplicated, checked against the inclusion
criteria, and mapped to ETCLOVG layers using public documentation.
9

Under review as submission to TMLR
2.6 Inclusion and Exclusion Criteria
A project was included when it satisfied three conditions: it was publicly documented, it implemented or
specified a concrete harness-level mechanism, and the available evidence was sufficient to assign at least
one ETCLOVG layer. This includes agent frameworks with reusable orchestration or tool-routing logic,
benchmarks that instantiate executable agent environments, sandboxes packaged for agent execution, and
memory, observability, evaluation, or governance systems that operate over agent state, traces, actions, or
policies. We excluded simple chatbot demos, prompt packs, thin model-client wrappers, static datasets or
leaderboards without an agent runtime, generic infrastructure components that were not agent-facing, and
productpageswhosetechnicalbehaviorcouldnotbeinspectedfrompublicdocumentation. Borderlinecases
were resolved by mechanism rather than label: a repository named as an “agent” was not sufficient for
inclusion, whileanevaluationorsandboxprojectwasincludedwhenitsuppliedreusableharnessmachinery.
2.7 Coding Protocol
Each retained project was coded against the seven ETCLOVG layers using the public artifact itself as
evidence: README files, documentation pages, papers, examples, release notes, and, when needed, repos-
itory structure. Coding was multi-label because many systems span layers; the primary layer marks the
mechanism most central to the artifact, while secondary layers are assigned only when the documentation
exposesanindependentcapabilityratherthananincidentaldependency. Thecurrentsnapshotusesasingle-
primary-coder protocol with author audit rather than a formal multi-coder agreement study, so we do not
report Cohen’s kappa or a comparable inter-annotator statistic. Ambiguous cases were revisited after the
fullsethadbeencoded,usingaconservativerule: ifthepublicevidencedidnotclearlyshowanagent-facing
mechanism, the layer assignment was withheld.
2.8 Limitations of the Corpus
The corpus should be read as a map of the visible agent-harness ecosystem, not as a census of all deployed
agent infrastructure. It is biased toward English-language sources, GitHub-visible projects, open-source
artifacts, and systems whose maintainers publish enough implementation detail for external coding. Com-
mercial production systems are underrepresented unless their engineering blogs, documentation, or SDKs
exposetherelevantmechanisms,andcoding-agentinfrastructureisoverrepresentedbecauseithasunusually
rich public traces: repositories, benchmarks, sandboxes, issue-to-pull-request workflows, and release notes.
The layer assignments also reflect public documentation rather than private architecture, so absence from a
layer means “not publicly evidenced” rather than “not implemented.”
2.9 Aggregate Analysis
The 170+ project mapping reveals an ecosystem that is broad but uneven. Execution, tool interfaces, life-
cycle orchestration, and verification have the densest visible coverage because coding, web, terminal, and
computer-use agents all require runnable environments, tool contracts, control loops, and repeatable evalu-
ation before they can be useful. Context and memory appear across many projects but are often embedded
inside larger frameworks rather than released as standalone harness components. Observability and gov-
ernance are thinner in open-source coverage and more often appear through commercial platforms, SDK
features, or engineering writeups, suggesting that operational control has matured later than runtime and
benchmark infrastructure. Cross-layer projects are increasingly common: the most complete systems com-
bine sandboxing, tool protocols, orchestration, tracing, evaluation, and permission controls, which supports
the central claim that harness engineering is an integrated systems problem rather than a collection of
isolated add-ons.
10

| Under review | as submission | to  | TMLR        |     |
| ------------ | ------------- | --- | ----------- | --- |
| 3 Execution  | Environment   |     | and Sandbox | (E) |
We open the layer-by-layer treatment with the Execution Environment and Sandbox (E) layer, the first of
the seven pillars of ETCLOVG (Claim 2 in §1). The systems we discuss are drawn from the 170+ project
| corpus that | supports | Claim 3. |     |     |
| ----------- | -------- | -------- | --- | --- |
Daytona(DaytonaPlatforms,Inc.,2024),E2B(E2B,2024),Modal(ModalLabs,2024),
|     | General-Purpose |     | Northflank(Northflank,2024), |     |
| --- | --------------- | --- | ---------------------------- | --- |
ManagedSandboxes
OpenSandbox(Alibaba,2026),DockerSandboxes(Docker,Inc.,2025)
|     | Computer-Use        |     | AnthropicComputerUse(Anthropic,2024b),CUA(Cua,2024),       |     |
| --- | ------------------- | --- | ---------------------------------------------------------- | --- |
|     | AgentInfrastructure |     | OSWorld(Xieetal.,2024)                                     |     |
|     | CodeandRepository   |     | Judge0(Došilović,2024),OpenAICodeInterpreter(OpenAI,2023), |     |
ExecutionSandboxes sandboxed.sh(Th0rgal,2026),langchain-sandbox(LangChain,2025c),Repo2Run(Huetal.,2025a)
tnemnorivnE xobdnaS&
noitucexE
|     | Framework-Integrated |     | OpenHands(Wangetal.,2025b),GoEX(Patiletal.,2024a),                         |     |
| --- | -------------------- | --- | -------------------------------------------------------------------------- | --- |
|     | Runtimes             |     | agent-infrasandbox(AgentInfra,2024),smolagentsexecutors(Roucheretal.,2025) |     |
|     | BrowserEvaluation    |     | WebArena(Zhouetal.,2024),VisualWebArena(Kohetal.,2024),                    |     |
|     | Environments         |     | BrowserGym(Chezellesetal.,2024),WorkArena(Drouinetal.,2024)                |     |
OS-LevelPermission Anthropicsandbox-runtime(Anthropic,2025g),ClaudeCodesandboxing(Anthropic,2025b),
IsolateGPT(Wuetal.,2025),AgentBound(Bühleretal.,2025),
|     | andRuntimeSecurity |     | transactionalsandboxing(Yan,2025) |     |
| --- | ------------------ | --- | --------------------------------- | --- |
SWE-ReX(SWE-agentTeam,2024),SWE-agent(Yangetal.,2024),
K8sAgentSandbox(KubernetesSIGApps,2025),
|     | SandboxAbstractions, |     | R2E-Gym(Jainetal.,2025),EnvScaler(Songetal.,2026), |     |
| --- | -------------------- | --- | -------------------------------------------------- | --- |
Training,andEvaluation
SandMLE(Zhouetal.,2026),
SandboxEscapeBench(Marchandetal.,2026),CIBER(Baetal.,2026)
Figure 6: Representative work on execution environments and sandboxes for LLM agents, organized by the
| chapter’s | sandbox categories. |     |     |     |
| --------- | ------------------- | --- | --- | --- |
| 3.1 Scope | and Concepts        |     |     |     |
3.1.1 Definition
Theexecutionenvironmentofanagentreferstotheinfrastructurelayerinwhichagentactionsarephysically
executed. InthecontextofLLMagents,theexecutionenvironmentandsandboxaretightlycoupledconcepts.
As a result, production agent systems almost invariably execute actions within a sandboxed environment.
| 3.1.2 | Why Sandboxing | Is Central | in the Agent | Era |
| ----- | -------------- | ---------- | ------------ | --- |
Sandboxing in the agent era is not merely a security measure inherited from traditional multiple tenant
code execution. It simultaneously serves three distinct purposes, and the combination of these three is what
elevates sandboxing from an operational detail to a first-class concern in agent harness design.
The first purpose is security. Agent sandboxing faces challenges beyond traditional multiple tenant code
execution. LLM-generated code is neither auditable nor predictable at scale, ruling out static review as a
primary defense. Agents execute autonomously over multiple steps, so human intervention is not available
at action execution time. Prompt injection attacks can repurpose an otherwise benign agent as a vector
for sandbox directed attacks, blurring the boundary between trusted user intent and hostile input. Recent
empiricalworkonsandboxescapesuggeststhattheseconcernsarenothypothetical,andwedeferquantitative
| evidence | to §3.3. |     |     |     |
| -------- | -------- | --- | --- | --- |
The second purpose is reproducibility. Long-horizon agent tasks and the evaluation harnesses that measure
them(§8)requiretheabilitytoresetexecutionstatetoaknownbaseline. ADockercontaineroramicroVM
can be destroyed and rebuilt on demand, whereas a developer’s workstation cannot, and this property is
whatmakessandbox-basedevaluationstandardssuchasSWE-benchJimenezetal.(2024)andOSWorldXie
etal.(2024)practical. Attrainingtime,whenasingletaskmaybereplayedhundredsoftimesacrossparallel
trajectories, the absence of a cheap reset mechanism is itself a scalability bottleneck.
The third purpose is liveness, and it is the one most specific to the agent era. Without a sandbox, every
potentially risky action that an agent wishes to execute, for example a file write, a package install, or an
outbound network call, must be gated by an explicit permission prompt to a human. At scale, this creates
11

Under review as submission to TMLR
two failure modes: users abandon the agent out of frustration, or they approve everything reflexively and
defeat the safety rationale of the prompts. A sandbox breaks this deadlock by defining a bounded region
within which the agent is authorized to act freely, shifting permission from a action question to a session
configuration. Anthropic reports that introducing sandboxing to Claude Code reduced permission prompts
by 84% while preserving safety Anthropic (2025b). Under this framing, a sandbox is simultaneously a cage
and a license, and the license aspect is what enables autonomous long horizon execution in the first place.
Of these three purposes, security is shared with traditional sandboxing, reproducibility is amplified in the
agent setting, and liveness is essentially new. Their combination is what justifies treating agent sandboxing
as a distinct research object rather than a downstream application of container technology.
3.2 Categories of Agent Sandboxes
Agentsandboxinfrastructurehasdiversifiedin2024to2026fromasmallsetofgeneral-purposeruntimesinto
severaldistinctproductcategories, eachoptimizedfordifferentagenttasktypes. Weorganizethelandscape
into seven categories along the axis of workload and use case, which we find most informative to a harness
designer choosing among systems. The orthogonal axis of isolation technology, including containers, user
space kernels such as gVisor Google (2018), microVMs such as Firecracker Agache et al. (2020) and Kata
Containers Kata ContainersProject (2017), WebAssembly, and OS-levelprimitives such as bubblewrapand
Seatbelt,isdiscussedasadesignpropertywithineachsubsectionratherthanasatop-levelcategory,because
the same isolation primitive is reused across different workloads. The seven categories are general-purpose
managedsandboxes(§3.2.1),computer-useagentinfrastructure(§3.2.2),code-specializedsandboxes(§3.2.3),
framework-integratedruntimes(§3.2.4),browserevaluationenvironments(§3.2.5),OS-levelpermissionsand-
boxes (§3.2.6), and sandbox abstraction layers (§3.2.7). The following subsections present each category.
3.2.1 General-Purpose Managed Sandboxes
General-purposemanagedsandboxesprovidecommercialoropen-sourcesandbox-as-a-serviceplatformsthat
exposearbitraryOCIcontainerimagesthroughtheAPIinterfaces,withshell,filesystem,network,andinter-
preter support for unspecified workloads. Representative systems include Daytona Daytona Platforms, Inc.
(2024), which pivoted from developer environments to agent sandboxes with sub-90ms cold-start provision-
ing; E2B E2B (2024), an agent sandbox built on Firecracker microVMs Agache et al. (2020); Modal Modal
Labs(2024),aPythonplatformusinggVisorGoogle(2018)withmassiveautoscaling;NorthflankNorthflank
(2024), a platform supporting Kata Containers Kata Containers Project (2017), Firecracker, and gVisor si-
multaneously; OpenSandbox Alibaba (2026) from Alibaba, an open source general-purpose sandbox; and
Docker Sandboxes Docker, Inc. (2025), Docker’s official microVM-based offering released in 2025.
Design decisions across this category converge on several patterns: ephemeral-by-default semantics with
optional persistent sessions, API interfaces exposed as SDKs in Python and TypeScript, and support for
arbitrary OCI images. Systems diverge on isolation strength and operational model. Daytona defaults to
container isolation with optional Kata Containers, while E2B, Modal, and Docker Sandboxes ship microVM
orgVisorisolationbydefault. Northflankuniquelyallowseachworkloadselectionamongbackends,reflecting
the industry recognition that no single isolation primitive fits all threat models. We observe a broader trend
from kernel container isolation toward dedicated-kernel microVM isolation, driven by the observation that
LLM-generated code has unpredictable syscall patterns that cannot be characterized in advance.
3.2.2 Computer-Use Agent Infrastructure
Computer-useagentinfrastructurerepresentsadistinctexecutionmodelinwhichagentsinteractwithgraph-
ical interfaces via simulated mouse, keyboard, and screen observation rather than through APIs or shell
commands. RepresentativesystemsincludeAnthropic’sComputerUseAnthropic(2024b),theflagshipcom-
mercial implementation enabling Claude to directly operate desktop environments; CUA Cua (2024), an
open-source computer-use agent infrastructure; and the VM-based environments provided by OSWorld Xie
et al. (2024), which serves dually as evaluation harness (§8) and as a reference computer-use sandbox.
12

Under review as submission to TMLR
These systems package a full or near full desktop environment (typically via Xvfb with a window manager
oracompleteVM)withinthesandbox,andexposepixel-coordinateandkeystrokeactionstotheagent. The
actionspaceissubstantiallylargerthaninAPI-basedcategories,butreliabilitydependsonvisualgrounding,
and the complete OS attack surface demands stronger isolation, typically microVM or full VM. Compared
withthemanagedsandboxesof§3.2.1,computer-usesandboxestradedensityandstartuplatencyforfidelity:
a full desktop environment is heavier to boot and harder to multiplex than a headless shell sandbox, but it
is the only execution model in which the agent can operate applications that expose no API.
3.2.3 Code-Specialized Sandboxes
Code-specialized sandboxes are lightweight, environments optimized for code generation, evaluation, and
data analysis rather than for general purpose shell access. Representative systems include Judge0 Došilović
(2024),acodeevaluationsandboxoriginallydesignedforjudgingandwidelyreusedasacomponentofcoding
agentevaluationpipelines;OpenAICodeInterpreterOpenAI(2023),theproduction-scalesandboxedPython
environmentunderlyingChatGPT’sAdvancedDataAnalysis;sandboxed.shTh0rgal(2026),ashellsandbox
for coding agents; and langchain-sandbox LangChain (2025c), which uses Pyodide Pyodide Contributors
(2018)compiledtoWebAssemblyandexecutedundertheDenoruntimetosandboxagent-generatedPython
locally without containers, a design also advocated by NVIDIA for client agentic workflows NVIDIA (2024).
Unlikethegeneralpurposesandboxesof§3.2.1,thesesystemspreinstallcompilersandinterpreters,defaultto
stateless request-level execution, and optimize for high concurrency parallelism. The design choice sacrifices
workload generality for startup speed, evaluation throughput, and simpler threat models. A notable sub-
trend is the shift from container-based code sandboxes toward WebAssembly-based ones: WebAssembly
offers capability-based security, deterministic execution, and microsecond-scale instantiation at the cost of a
restricted Python standard library and reduced native extension support.
3.2.4 Framework-Integrated Runtimes
Framework-integratedruntimesareexecutionenvironmentsbundledinsideabroaderagentframeworkrather
than exposed as standalone sandbox products. They ship together with the framework’s orchestration
loop, tool registry, and prompt conventions, and cannot be consumed independently without adopting the
surrounding framework. Representative systems include the OpenHands runtime Wang et al. (2025b), a
Docker sandboxed environment that integrates bash, IPython, a Chromium browser, and an API server
into a single image; agent infra sandbox Agent Infra (2024), an explicit all-in-one design packaging browser,
shell, filesystem, MCP, and VSCode into one environment; and the executor layer of smolagents Roucher
etal.(2025),whichprovidesinframeworkimplementationsoflocal,Docker,E2B,Modal,andWebAssembly
execution.
The defining trade-off in this category is between bundle and compose: framework-integrated runtimes
prioritize out of the box capability coverage at the cost of larger image size, slower startup, and tight
coupling to one framework’s abstractions. In contrast, the general-purpose sandboxes of §3.2.1 take the
opposite approach of minimal environments composed via external abstractions. Whether the composition
approach displaces bundled runtimes in the long run depends on whether standards such as MCP reduce
the penalty of assembling capabilities at runtime rather than at build time.
3.2.5 Browser Evaluation Environments
Browser evaluation environments occupy a dual role as both sandboxes and evaluation harnesses. Repre-
sentative systems include WebArena Zhou et al. (2024), a self-hosted cluster of realistic web applications
paired with Playwright-based interaction; VisualWebArena Koh et al. (2024), which extends WebArena
with multimodal visual grounding tasks; and BrowserGym Chezelles et al. (2024), which together with
WorkArena Drouin et al. (2024) provides a standardized gym-style interface for browser-based agent execu-
tion and benchmarking.
These systems provide isolated web execution environments (sandbox role) while simultaneously supplying
reproducibletaskdefinitionswithautomatedevaluation(harnessrole). Thedualfunctiondistinguishesthem
13

Under review as submission to TMLR
fromthecomputer-usecategoryof§3.2.2,whichoperatesatthedesktopratherthanthebrowserlevel,andit
createsadirectinterfacebetweentheexecutionenvironmentdiscussedhereandtheevaluationinfrastructure
discussed in §8. Browser environments also expose a distinct threat surface: because the browser ingests
untrusted web content, they are a natural substrate for studying indirect prompt injection and multimodal
red-teaming attacks against agents Debenedetti et al. (2024); Greshake et al. (2023); Zhang et al. (2026a);
Wei et al. (2026).
3.2.6 OS-Level Permission Sandboxes
OS-level permission sandboxes implement fine-grained filesystem and network isolation using operating-
systemprimitives(bubblewraponLinux,SeatbeltonmacOS,orseccomp-bpfforsyscallfiltering)ratherthan
containers,VMs,oruser-spacekernels. Theyaresubstantiallylighterthancontainersandboxeswhileprovid-
ing directory and domainaccess control. Representativesystems include Anthropic’s sandbox-runtimeAn-
thropic (2025g), an open-source npm package that wraps arbitrary commands with filesystem and network
allowlists enforced via bubblewrap and a local HTTP/SOCKS5 proxy; the sandboxing features built into
ClaudeCodeitselfAnthropic(2025b), whichconsumethatruntimetorestrictthebashtool’sfilesystemand
network access to configured boundaries; and IsolateGPT Wu et al. (2025), a research system that applies
seccomp and setrlimit to enforce execution isolation across tool-calling LLM applications.
The design philosophy of this category is permission, not partition: the goal is not to provide a fresh
OS image for every session but to give an agent a narrowed view of the existing host so that prompt-
injected or hallucinated commands cannot modify sensitive files or exfiltrate data. Anthropic reports that
such boundaries reduced permission prompts in Claude Code by 84% while preserving safety Anthropic
(2025b),illustratingtheproductivitymotivationforOS-levelsandboxing: permissionpromptsarethemselves
a liveness failure in long-horizon agent execution. Because the host kernel is shared, OS-level permission
sandboxes offer weaker isolation against adversarial code than microVM-based managed sandboxes (§3.2.1);
they are appropriate when the threat model is prompt injected rather than fully adversarial code.
3.2.7 Sandbox Abstraction Layers
Sandbox abstraction layers are not sandboxes themselves but interfaces that unify multiple sandbox back-
ends behind a single API, allowing a harness to switch execution substrates without rewriting agent code.
Representative systems include SWE-ReX SWE-agent Team (2024), a runtime interface developed by the
SWE-agent team Yang et al. (2024) that unifies Docker, AWS Fargate, Modal, and Daytona as interchange-
able backends; the executor interface of smolagents Roucher et al. (2025), which exposes local, e2b, modal,
docker, blaxel, and wasm as a single parameterized executor_type; and the Agent Sandbox Kubernetes
SIG Apps (2025) project under Kubernetes SIG Apps, which introduces a Sandbox CRD and controller
exposing gVisor and Kata Containers as pluggable isolation backends through a declarative API.
The emergence of this category reflects a maturing understanding that execution infrastructure should be
replaceable. A harness that hard-codes a particular sandbox API couples its orchestration logic to one
vendor’s ephemeral product; an abstraction layer decouples what the agent runs from where it runs. We
observe a convergence between research projects (SWE-ReX), framework-embedded interfaces (smolagents
executors), and emerging infrastructure standards (the Kubernetes agent-sandbox CRD), suggesting that
sandboxabstractionisbecomingadistinctlayeroftheagentharnessstackratherthanafeatureofindividual
systems.
Synthesis. Across the seven categories, three cross-cutting trends are visible. First, the field is bifur-
cating along isolation strength rather than converging: managed sandboxes (§3.2.1) are migrating from
shared-kernel containers toward dedicated-kernel microVMs, while OS-level permission sandboxes (§3.2.6)
dispense with separate environments entirely and instead narrow the host’s view. The middle ground of
plain Docker containers is being squeezed from both ends, and the choice between the two extremes re-
flectsthethreatmodel(fullyadversarialcodeversusprompt-injectedbutotherwisecooperativecode)rather
than a universal technology preference. Second, evaluation robustness is emerging as a first-class concern:
container-escapebenchmarkssuchasSandboxEscapeBenchMarchandetal.(2026)andsecuritybenchmarks
for code-interpreter agents such as CIBER Ba et al. (2026) show that sandbox configurations currently de-
14

Under review as submission to TMLR
ployedinproductionarepartiallybypassablebyfrontiermodels. Third,thefieldisseparatinginfrastructure
level isolation (what this section covers) from semantic or capability-level isolation at the tool calling layer.
CaMeL’s control flow integrity design Debenedetti et al. (2025) and Progent’s programmable privilege con-
trol Shi et al. (2025a) exemplify the latter, and belong to the tool-use chapter (§4) rather than to sandbox
infrastructure proper. These two lines are complementary: an infrastructure sandbox constrains the blast
radius of an action once it is executed, while semantic isolation constrains which actions are permitted in
the first place. A complete agent harness requires both.
3.3 Threat Model and Sandbox Escape
Sandboxing agent execution faces both traditional container-level threats (container escape, side channels,
resourceexhaustion)andagentspecificthreatclassesthatamplifyclassicalconcerns. First,promptinjection
attacks allow external input, such as retrieved web pages, tool responses, or file contents, to hijack agent
behavior and initiate malicious sandbox operations. Second, goal misalignment can cause the agent itself to
activelyattemptsandboxescapeasaninstrumentalsubgoal. Third,compositionalamplificationoccurswhen
agents with multiple tools access allow a single sandbox weakness to cascade across integrated capabilities.
Empirical evidence on sandbox escape in the agent setting is limited but concerning. Sandbox-
EscapeBench Marchand et al. (2026) evaluates frontier LLMs in a nested sandbox capture-the-flag setting
and reports 15% to 35% escape success rates against Docker-based containers, depending on container con-
figuration. The benchmark covers a spectrum of escape mechanisms, including misconfiguration, privilege
allocation mistakes, kernel flaws, and runtime or orchestration weaknesses, and its results establish that
the threat is realized rather than merely theoretical even at current model capabilities. Defense research
remains in early stages. IsolateGPT Wu et al. (2025) proposes an execution isolation architecture for LLM-
based agentic systems, reporting under 30% performance overhead for three-quarters of tested queries while
preventing cross-application data leaks. Transactional sandboxing approaches Yan (2025) provide rollback-
based protection, reporting approximately 14.5% overhead with high interception rates for risky commands.
AcomplementaryperspectiveisofferedbyLLM-in-SandboxChengetal.(2026), whicharguesthatminimal
ratherthanmaximallycapablesandboxenvironmentsreduceboththeattacksurfaceandunnecessaryagent
complexity.
Taken together, these results expose a gap between offensive and defensive progress. Offensive evaluation
has produced a concrete and reproducible benchmark, whereas defensive work is still fragmented across
isolated prototypes that differ in threat model, evaluation protocol, and baseline assumptions. An agent-
native runtime security framework that systematically addresses prompt injection, goal misalignment, and
compositional amplification under a common evaluation methodology is an open research direction, which
we revisit in §12.1.
3.4 Deployment Modes
Agentsandboxinfrastructurehasdiversifiedacrossdeploymentmodesbeyondtheoriginalself-hostedDocker
pattern. Three modes coexist in current practice. In the self-hosted mode, developers manage sandbox in-
frastructuredirectly,whichisthedefaultpatternforOpenHandsandSWE-agent. Inthecloud(SaaS)mode,
sandbox as a service providers handle infrastructure, as exemplified by E2B, Modal, and Daytona Cloud. In
the hybrid or bring-your-own-cloud (BYOC) mode, agent logic and sandbox execution are decoupled across
environments; examples include the OpenHands SDK’s Local and Remote Workspace abstraction Wang
et al. (2025c) and the BYOC offerings of E2B and Northflank.
The evolution across these modes has been driven by two complementary forces. On one hand, practitioner
reportsframethedeploymentchoicealongthreeaxesoflatency,security,andscalabilityAnthropic(2025b;f).
Self-hosted sandboxes offer lowest latency and tightest iteration loops but bear the full operational burden;
cloud sandboxes invert this trade-off, providing elastic scale and managed security at the cost of network
round-trips; hybrid modes attempt to keep sensitive data local while delegating execution capacity. On the
otherhand,organizationalconstraintssuchasdataresidency,compliance,andauditabilitypushdeployments
toward hybrid architectures even when latency and scalability would favor a single mode solution.
15

| Under review | as submission | to TMLR |     |     |     |     |
| ------------ | ------------- | ------- | --- | --- | --- | --- |
Inobservedpractice,self-hostedsandboxespredominateininteractivedevelopmentandsingle-tenantscenar-
ios,whilecloudsandboxesaremorecommoninmultipletenantsandlargescaledeployments. Hybridmodes
are emerging specifically for scenarios where compliance or data-locality requirements coexist with the need
for large pools of ephemeral execution capacity. Systematic empirical comparison across these modes under
realistic agent workloads remains absent, and we treat it as part of the broader runtime agenda in §12.1.
3.5 Summary
Execution environments are the physical substrate of an agent harness: they provide the security boundary,
theresetmechanismforreproducibleevaluationandtraining,andtheboundedregioninwhichlong-horizon
agents can act without command human approval. The seven categories surveyed in this section show that
the design space is now shaped less by a single isolation primitive than by workload fidelity, threat model,
and operational mode. Managed sandboxes and computer-use environments emphasize strong isolation
and realistic execution; code-specialized and browser environments emphasize throughput and evaluation
structure; framework-integrated runtimes bundle capability for convenience; OS-level permission sandboxes
narrow local authority; and abstraction layers make the substrate replaceable.
This design space creates a recurring tension between capability, control, and cost. High risk workloads
pushtowardmicroVMsandmanagedclouds,interactivelocalworkflowspushtowardlightweightpermission
boundaries, and large scale training or evaluation pushes toward fast resettable substrates. The unresolved
questions about runtime defense, economics, portability, bundle versus compose design, and cross layer
couplingarethereforenotisolatedexecutionlayerfootnotes; theyreappearassurvey-wideopenproblemsin
§12.1.
| 4 Tool | Interface | and Protocol | Layer (T) |     |     |     |
| ------ | --------- | ------------ | --------- | --- | --- | --- |
The Tool Interface and Protocol layer (T) is the second pillar of ETCLOVG (Claim 2 in §1). The protocols,
descriptions, and registries we discuss are drawn from the 170+ project corpus that supports Claim 3.
|               |                |                       | M C P ( M o d e       | l C o n t e x t P r o t o c o l , 2 | 0 2 5 b ; c ), A 2 A ( A 2 A        | P r o j e c t , 2 0 2 5 ) ,           |
| ------------- | -------------- | --------------------- | --------------------- | ----------------------------------- | ----------------------------------- | ------------------------------------- |
|               | P r o          | t oc o l a n d        | F u n ct i o n C a    | l li n g ( O p en A I , 2 0 2 6 c   | ) , O p e n A P I ( O p e n A       | P I I n i t i a t i v e , 2 0 2 5 ) , |
|               | Inte r fa      | c e S t a n d ards    | A G E N T S . m d     | ( a g e n t s m d , 2 0 2 5 ) ,     | I n t e r o p . S u r v e y ( E h t | es h a m e t a l . , 2 0 2 5 )        |
|               |                |                       | E a s y T o o l ( Y   | u a n e t a l . , 2 0 2 5 ), M C    | P - Z e r o ( F e i e t a l . , 2   | 0 2 5 ) , A nyTool(Duetal.,2024),     |
| ecafretnIlooT | ToolDe s c rip | t i o n , D iscovery, | C R A F T ( Y u       | a n e t a l. , 2 0 2 3 ) , M e t    | a T o o l ( H u a n g e t a l. ,    | 2 0 2 3 ) ,                           |
| locotorP&     | a n d          | S e l e c ti on       |                       |                                     |                                     |                                       |
|               |                |                       | To o lR e g i s t r y | ( D i n g , 2 0 2 5 ) , T o o lR    | e t ( S h i e t a l. , 2 0 2 5 b    | )                                     |
Toolformer(Schicketal.,2023),Gorilla(Patiletal.,2024b),ToolLLM/ToolBench(Qinetal.,2024),
|     | Tool-AugmentedTraining |     | ToolkenGPT(Haoetal.,2023),CREATOR(Qianetal.,2023b),                  |     |     |     |
| --- | ---------------------- | --- | -------------------------------------------------------------------- | --- | --- | --- |
|     | andIntegration         |     | AgenticCodeReasoning(Ugare&Chandra,2026),LangChain(LangChain,2026c), |     |     |     |
SemanticKernel(Microsoft,2026),smolagents(HuggingFace,2026)
|     | S c a la   | bil i ty a n d   | R e A c t ( Y a o   | e t a l ., 2 0 2 3 ) , L L M C o    | m p i le r ( K im e t a l. , 2  | 0 2 4 ) , E 2 B ( E 2 B , 2 0 2 4 ),                    |
| --- | ---------- | ---------------- | ------------------- | ----------------------------------- | ------------------------------- | ------------------------------------------------------- |
|     | Ses si o n | M a n ag e m ent | M C P C o d e E     | x e c u t i o n ( A n t h r o p i c | , 2 0 2 5 f ) , B F C L ( P a t | i l e t a l ., 2 0 2 5 ) ,                              |
|     |            |                  | St a b le T o o l B | e n c h ( G u o e t a l ., 2 0 2    | 4 ) , A P I - B a n k (L i e t  | a l . , 2 0 2 3 b ), T a s k B e n c h (Shenetal.,2024) |
Figure 7: Representative work on tool interfaces and protocols for LLM agents, organized by the chapter’s
| tool-layer | categories. |     |     |     |     |     |
| ---------- | ----------- | --- | --- | --- | --- | --- |
The tool interface and protocol layer defines how an agent discovers capabilities, represents callable affor-
dances, and executes actions across heterogeneous runtime boundaries. In practice, this layer sits at the
fault line between two competing objectives: increasing capability coverage by exposing more tools, versus
preservingdecisionqualitybykeepingtheactionspaceandpromptfootprintsmall. Recentengineeringguid-
ance from production agent systems repeatedly reports that oversized tool menus can degrade reliability,
increase token overhead, and amplify planning errors (Anthropic, 2025d; OpenAI, 2026c).
We organize this layer into four complementary directions: protocol and interface standards; tool descrip-
tion, discovery, and selection; tool-augmented model training and integration; and scalability and session
management.
16

| Under review | as  | submission | to        | TMLR |     |     |     |     |     |     |     |
| ------------ | --- | ---------- | --------- | ---- | --- | --- | --- | --- | --- | --- | --- |
| 4.1 Protocol | and | Interface  | Standards |      |     |     |     |     |     |     |     |
MCPhasbecomethemostvisibletool-integrationsubstrateforcodingandenterpriseagents,withanexplicit
host-client-serverarchitectureandJSON-RPC-basedtypedexchangeoftools,resources,andprompts(Model
Context Protocol, 2025b;c;a). The practical value of MCP is not only schema-level interoperability, but also
ecosystem liquidity: agent builders can reuse an expanding server catalog instead of implementing custom
| connectors | for each | deployment. |     |     |     |     |     |     |     |     |     |
| ---------- | -------- | ----------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
A2Atargetsadifferentbutadjacentboundary. Ratherthanexposingtoolstooneagentprocess,itstandard-
izes communication among opaque agentic applications, including discovery through Agent Cards, support
for synchronous and streaming interactions, and long-running task collaboration (A2A Project, 2025). Re-
cent protocol surveys place MCP and A2A in complementary roles: MCP primarily for tool/context access,
A2Aforinter-agentdelegationandcollaboration(Ehteshametal.,2025). Amoreusefulorganizingprinciple,
in our view, is to categorize tool/interface standards by the integration boundary they cross rather than by
vendor lineage or release timeline. Under this lens, four boundaries emerge: Model↔Function (structured
invocation), Agent↔External capability (runtime-to-tool decoupling), Agent↔Agent (cross-process delega-
tion), and Agent↔Repo/environment (version-controlled policy). Table 1 summarizes this view and makes
explicit why several widely compared standards (e.g., MCP vs. A2A, or Function calling vs. OpenAPI)
| occupy non-overlapping |     |     | roles in | a single | harness. |     |     |     |     |     |     |
| ---------------------- | --- | --- | -------- | -------- | -------- | --- | --- | --- | --- | --- | --- |
Function-calling schemas and API-description standards remain foundational building blocks in this layer.
OpenAI-style function calling operationalizes tool invocation through JSON schema and explicit call/return
turns (OpenAI, 2026c); OpenAPI provides a language-agnostic, machine-readable API contract that many
agentframeworksuseasasourcefortoolgenerationandvalidation(OpenAPIInitiative,2025). Inaddition,
repository-level instruction files such as AGENTS.md and AGENT.md provide a lightweight alternative for
encoding tool usage and workflow constraints directly in version control, reducing setup friction for code
| agents (agentsmd, |     | 2025; | agentmd, | 2025). |     |     |     |     |     |     |     |
| ----------------- | --- | ----- | -------- | ------ | --- | --- | --- | --- | --- | --- | --- |
Table 1: Tool/interface standards arranged along the integration boundary they cross (rows) and four
harness-relevantcapabilityaxes(columns). =first-classsupport; =partialorconvention-level; =out
| of scope. | References   | appear        | in         | the surrounding |           | text.    |                  |         |                  |              |                  |
| --------- | ------------ | ------------- | ---------- | --------------- | --------- | -------- | ---------------- | ------- | ---------------- | ------------ | ---------------- |
|           |              |               |            |                 | (cid:32)  |          | (cid:71)(cid:35) |         |                  |              | (cid:35)         |
| Boundary  |              | Standard      |            |                 |           | Wire     | Typed            | Runtime | disc.            | Long-running |                  |
| Model ↔   | Function     | Function      |            | calling         |           | JSON     |                  |         |                  |              |                  |
|           |              |               |            |                 |           |          | (cid:32)         |         | (cid:35)         |              | (cid:35)         |
|           |              | MCP           |            |                 |           | JSON-RPC |                  |         |                  |              |                  |
| Agent ↔   | Capability   |               |            |                 |           |          |                  |         |                  |              |                  |
|           |              | OpenAPI       |            |                 |           | HTTP     | (cid:32)         |         | (cid:32)         |              | (cid:71)(cid:35) |
|           |              |               |            |                 |           |          | (cid:32)         |         | (cid:71)(cid:35) |              | (cid:35)         |
|           |              | A2A           |            |                 |           | JSON-RPC |                  |         |                  |              |                  |
| Agent ↔   | Agent        |               |            |                 |           |          |                  |         |                  |              |                  |
|           |              | ACP           | / ANP      |                 |           | HTTP     | (cid:32)         |         | (cid:32)         |              | (cid:32)         |
|           |              |               |            |                 |           |          | (cid:32)         |         | (cid:32)         |              | (cid:32)         |
| Agent ↔   | Repo /       | env AGENTS.md |            | / AGENT.md      |           | Markdown |                  |         |                  |              |                  |
|           |              |               |            |                 |           |          | (cid:35)         |         | (cid:71)(cid:35) |              | (cid:35)         |
| 4.2 Tool  | Description, |               | Discovery, | and             | Selection |          |                  |         |                  |              |                  |
Onceprotocolsdefinehow callsaremade, thenextbottleneckiswhich toolsshouldbesurfacedandselected
at each step. A growing line of work studies tool documentation quality, retrieval, and dynamic candidate
pruning. EASYTOOL analyzes the challenge of selecting suitable tools from large inventories (Yuan et al.,
2025). AnyTool and CRAFT focus on reducing manual specification burden by automatically constructing
orrefiningtool-usepipelines(Duetal.,2024;Yuanetal.,2023). MetaToolbenchmark-styleevaluationsshow
that tool retrieval and invocation quality can diverge substantially across domains and query forms (Huang
et al., 2023). More recent work such as MCP-Zero, ToolRet, and ToolRegistry emphasizes retrieval-aware
orchestration and registry quality as first-order determinants of downstream agent success (Fei et al., 2025;
Shi et al., 2025b; Ding, 2025). A closely related direction extends tool selection to reusable skills, where
agentsmustidentifyrelevantproceduralmodulesratherthanonlycompactAPIschemas. SkillRouter(Zheng
17

| Under review | as submission |     | to TMLR |     |     |     |
| ------------ | ------------- | --- | ------- | --- | --- | --- |
et al., 2026) and SkillRet (Cho et al., 2026) both study this skill-selection problem at scale, highlighting the
| need to retrieve | the | right | skill from | large | and overlapping | skill libraries. |
| ---------------- | --- | ----- | ---------- | ----- | --------------- | ---------------- |
At the system level, these results reinforce two design principles. First, “fewer but better tools” often out-
performs brute-force tool exposure because it shrinks both prompt entropy and planner branching. Second,
discovery pipelines must be adaptive: static, global tool lists do not scale to rapidly evolving repositories or
| multi-tenant       | enterprise | deployments. |     |             |     |     |
| ------------------ | ---------- | ------------ | --- | ----------- | --- | --- |
| 4.3 Tool-Augmented |            | Training     | and | Integration |     |     |
The third direction shifts from runtime orchestration to model capability acquisition. Toolformer demon-
stratesself-supervisedaugmentationforlearningwhenandhowtoinsertAPIcallsduringgeneration(Schick
et al., 2023). Gorilla and ToolLLM/ToolBench extend this line with larger tool corpora, instruction-tuning
pipelines, and execution-centric supervision for API use (Patil et al., 2024b; Qin et al., 2024). ToolkenGPT
and CREATOR explore token-level or controller-style integration to improve call formatting fidelity and
| planning | stability (Hao | et  | al., 2023; | Qian | et al., 2023b). |     |
| -------- | -------------- | --- | ---------- | ---- | --------------- | --- |
Inproductionharnesses,thesemodelsideadvancesaretypicallypairedwithframeworklevelruntimestacks,
such as LangChain, Semantic Kernel, and smolagents, that provide memory abstractions, routing middle-
ware, andtooladapters(LangChain,2026c;Microsoft,2026;HuggingFace,2026). Thecodingagentsetting
also exposes a second, more semantic class of tools: static analyzers, type checkers, solver backed verifiers,
proof assistants, and patch equivalence or fault localization checkers. Ugare & Chandra (2026) frame this
space as reasoning: an agent explores a repository and reasons about code behavior with-
agentic code
out necessarily executing the code. Their semi formal reasoning method sits between unstructured chain
of thought and fully formal verification by forcing the agent to state premises, trace program paths, and
derive explicit conclusions, improving patch equivalence verification, fault localization, and code question
answering. For the tool layer, the implication is that automated reasoning tools should return evidence
bearing artifacts, such as traces, proof obligations, counterexamples, or structured certificates, rather than
only black box yes/no answers. The combined evidence suggests that tool competence is jointly determined
bypretrainingandfinetuningsignals,interfaceschemaquality,andruntimeselectionpolicy;improvingonly
| one component   | yields | limited | gains.     |     |     |     |
| --------------- | ------ | ------- | ---------- | --- | --- | --- |
| 4.4 Scalability | and    | Session | Management |     |     |     |
Arecurringoperationalchallengeissessionmanagementunderlonghorizons. Statefultoolsessionsimprove
continuity but increase bookkeeping complexity, especially when calls are parallelized or delegated across
multiple agents. Failure modes include stale handles, inconsistent tool state across retries, and context-
window saturation from verbose tool traces. Effective harness design therefore requires explicit lifecycle
controls for tool sessions, bounded tool context injection, and observability hooks that can attribute errors
| to either | planner logic | or  | interface/protocol |     | failures. |     |
| --------- | ------------- | --- | ------------------ | --- | --------- | --- |
Finally,ecosystem-levellandscapecurationcanhelppractitionersquicklymapavailableprotocolandtooling
options,butbenchmark-groundedcomparisonremainsessentialfordecidingwhichprotocolandtool-routing
| strategy should | be adopted |        | in a given | deployment. |     |     |
| --------------- | ---------- | ------ | ---------- | ----------- | --- | --- |
| 5 Context       | and        | Memory | Management |             | (C) |     |
Context and Memory Management (C) is the layer where prompt and context engineering meet harness
engineering. We treat it as the third pillar of ETCLOVG (Claim 2 in §1), with examples drawn from the
| 170+ project | corpus | that | supports | Claim | 3.  |     |
| ------------ | ------ | ---- | -------- | ----- | --- | --- |
18

| Under review | as submission | to TMLR |     |     |     |
| ------------ | ------------- | ------- | --- | --- | --- |
EffectiveContextEngineering(AnthropicAppliedAITeam,2025),
|     | Short-TermActive |     | ManusContextEngineering(ManusTeam,2025),                     |     |     |
| --- | ---------------- | --- | ------------------------------------------------------------ | --- | --- |
|     | ContextWindow    |     | ContextManagement(Anthropic,2025c),AgentSkills(Koylan,2025), |     |     |
Context-Space(context-space,2025)
StructuredNote-Taking(AnthropicAppliedAITeam,2025),
|     | Mid-TermSessionState    |     | Planning-with-Files(OthmanAdi,2025),Trellis(mindfold-ai,2025), |     |     |
| --- | ----------------------- | --- | -------------------------------------------------------------- | --- | --- |
|     | andCross-RunPersistence |     | Claude-Mem(thedotmack,2025),                                   |     |     |
yromeM&txetnoC
Everything-Claude-Code(affaan-m,2025)
tnemeganaM
MemGPT(Packeretal.,2023),GenerativeAgents(Parketal.,2023),
|     | Long-TermPersistent |     | MemoryBank(Zhongetal.,2024),                                               |     |     |
| --- | ------------------- | --- | -------------------------------------------------------------------------- | --- | --- |
|     | MemorySystems       |     | Mem0(Chhikaraetal.,2025),A-MEM(Xuetal.,2025),Hindsight(Vectorize.io,2025), |     |     |
Honcho(PlasticLabs,2025),CQ(MozillaAI,2025)
ContextCompaction(AnthropicAppliedAITeam,2025),
|     | L o n g -H     | o r iz o n   | S u b - A g en t C  | o n t e x t I s o la t i o n ( A n | t h ro p ic , 2 0 2 5e), |
| --- | -------------- | ------------ | ------------------- | ---------------------------------- | ------------------------ |
|     |                |              | M a n u s C o n t   | e x t S h a r i n g ( M a n u s    | T e a m , 2 0 2 5 ),     |
|     | Con t e x t Te | c h n iq ues | H a r n e s s D e s | ig n ( A n t h r o p i c , 2 0 2 6 | c ) ,                    |
EffectiveHarnesses(Anthropic,2025d)
LostintheMiddle(Liuetal.,2024),ContextRot(Hongetal.,2025),
|     | ContextDrift |     | HarnessBoundary(Bowne-Anderson&Huber,2026),        |     |     |
| --- | ------------ | --- | -------------------------------------------------- | --- | --- |
|     | andLimits    |     | MemBench(Tanetal.,2025),MemoryArena(Heetal.,2026), |     |     |
IncrementalMemoryEvaluation(Huetal.,2025b)
Figure 8: Representative work on context and memory management for LLM agents, organized by the
| chapter’s | context-layer categories. |     |     |     |     |
| --------- | ------------------------- | --- | --- | --- | --- |
This layer governs what information the model sees at each step of execution and how knowledge persists
across turns and sessions. The core engineering problem is simple to state: give the model exactly the
right information at each step, nothing more. Too little context and the agent lacks the state needed to act
correctly. Too much and performance degrades in ways that are measurable, consistent across models, and
| not fully understood. |     |     |     |     |     |
| --------------------- | --- | --- | --- | --- | --- |
We structure this section around time horizon. Section 5.1 establishes why context requires active manage-
ment rather than passive accumulation. Section 5.2 defines context engineering as a discipline distinct from
prompt engineering. Sections 5.3 through 5.5 cover the three memory tiers that have emerged in production
practice: theactivecontextwindow(short-term),session-levelpersistence(mid-term),andcross-sessionstor-
age (long-term). Section 5.6 addresses the coordination problem that arises when agents run for hundreds
| of turns. Section | 5.7 closes   | with what     | remains unsolved. |     |     |
| ----------------- | ------------ | ------------- | ----------------- | --- | --- |
| 5.1 Why           | Context Must | Be Engineered |                   |     |     |
Larger context windows do not solve the memory problem. Understanding why requires looking at the
architecture.
Quadratic attention cost. The transformer’s self-attention mechanism computes pairwise relationships
between every token in the context (Vaswani et al., 2017). For tokens, this produces n2 pairwise weights;
n
computeandmemoryscalequadraticallywithcontextlength. EngineeringtechniquessuchasFlashAttention
and position-encoding interpolation reduce constant factors, but the quadratic structure is architectural.
Doubling the context does not double cost – it quadruples it. This makes the context window a scarce
resource.
Architecturalcostalonedoesnotexplainwhymodelsfailonlongcontexts
TheU-shapedattentioncurve.
evenwhencomputationisaffordable. Liuetal.(2024)providedthekeyempiricalresult: onmulti-document
questionansweringwith20inputdocuments,accuracydropsbymorethan30%whentherelevantdocument
sits in the middle of the context, compared to placing it at the start or end. This U-shaped performance
curveholdsacrossmodels,tasks,andcontextlengths,includingmodelstrainedspecificallyonlongcontexts.
The practical implication is direct: information placement matters as much as information presence. An
agent that retrieves the right content but positions it poorly gains little from the retrieval.
Hongetal.(2025)evaluated18frontiermodels,includingGPT-4.1,ClaudeOpus4,
| Context | rot at scale. |     |     |     |     |
| ------- | ------------- | --- | --- | --- | --- |
Gemini 2.5, and Qwen3, under controlled conditions designed to isolate input length from task difficulty.
Everymodeldegradedasinputgrew. Thedegradationwasnon-uniformandtask-specific. Semanticallyam-
biguousqueries,wheretherelevantpassagedoesnotlexicallymatchthequestion,showedsteeperdegradation
than exact-match queries, pointing to a compound failure: the model cannot localize relevant information,
19

Under review as submission to TMLR
and then cannot reason over it once located. The degradation also begins well before windows are full. A
model rated for 200K tokens may show significant performance loss at 50K. This phenomenon, which Hong
et al. (2025) call context rot, is not an edge case. It is the normal operating condition for any agent that
accumulates tool results, intermediate reasoning, and file contents over multiple steps.
Taken together, these results establish that context management cannot be an afterthought. Every decision
aboutwhattoinclude,wheretoplaceit,andwhentoremoveithasdirectconsequencesforagentreliability.
5.2 From Prompt Engineering to Context Engineering
Theshiftfromprompt engineering tocontext engineering reflectsashiftinscope(Karpathy,2025). Prompt
engineering optimizes a largely static text input to a single model call. In vision, the same framing extends
to continuous learnable tokens: visual prompt tuning prepends a small set of trainable vectors to the patch
sequenceofafrozenvisiontransformer,adaptingittodownstreamtaskswhileupdatinglessthan1%ofmodel
parameters(Jiaetal.,2022;Xiaoetal.,2025). Boththetextandvisionvariantssharethecorecharacteristic
of prompt engineering: a fixed, single-call optimization targeting one input modality. Context engineering
optimizes the full information state available to the model at each inference step across a multi-step task.
Anthropic’s applied AI team defines it as “the set of strategies for curating and maintaining the optimal
set of tokens during LLM inference, including all the other information that may land there outside of the
prompts” (Anthropic Applied AI Team, 2025). The guiding principle that follows is finding the smallest
set of high-signal tokens that maximizes the probability of the desired outcome at each step. This principle
drives every technique in this section. Progressive disclosure loads information just in time rather than
upfront. Compaction removes tokens that have served their purpose. Memory retrieval pulls in only the
records most relevant to the current task.
What context contains. In a deployed agent, context at inference time includes the system prompt and
behavioral instructions, tool definitions and schemas, prior turn history, tool call results from the current
trajectory,retrieveddocumentsormemoryrecords,andanydynamicallyinjectedworkingstate. Allofthese
competeforthesamefiniteattentionbudget. Contextengineeringmeansmakingexplicitchoicesabouteach
component at each step, rather than letting them accumulate unchecked.
The maturation of this practice is visible in the ecosystem. First-principles handbooks (Kimai, 2025) and
curated surveys (Meirtz, 2025) now treat context engineering as a discipline in its own right. The three-tier
memory architecture, covering the active context window, session-level state, and cross-session storage, has
emerged as the dominant organizing framework. It maps directly onto the classical memory hierarchy of
operating systems, which provides both useful intuition and a vocabulary for matching the right technique
to the right time horizon.
5.3 Short-Term: Managing the Active Context Window
Short-term context management governs what the model sees during a single inference step or a short
sequence of steps within a session. These decisions have the most immediate effect on model behavior and
carry the highest cost when made poorly.
Systempromptcalibration. Thesystempromptestablishestheagent’sbehavioralenvelopeandconsumes
afixedbudget oneverycall. AnthropicAppliedAI Team(2025) characterizethedesignchallengeas finding
therightaltitude: promptsthataretoospecificintroducebrittle,maintenance-heavylogic;promptsthatare
toovagueleavethemodelwithoutconcreteguidance. Inpractice,effectivesystempromptsareorganizedinto
clearly delineated sections for background, instructions, tool guidance, and output format, using XML tags
or Markdown headers to separate them. The recommended workflow is to start with a minimal prompt on
thebestavailablemodel,identifyfailuremodesempirically,thenaddtargetedinstructionstoaddressspecific
gaps. Preemptively enumerating every edge case tends to bloat prompts without improving reliability.
Token-efficient tool design. Tool definitions are a major context consumer. Every schema, name, de-
scription, and parameter type is injected at every call. A large tool set can consume tens of thousands of
tokensbeforetheagentreadstheuserrequest. Theprinciplethatemergesfromproductiondeploymentsisto
20

| Under review | as submission | to TMLR |     |     |     |     |     |     |
| ------------ | ------------- | ------- | --- | --- | --- | --- | --- | --- |
prefer fewer, more expressive tools over a large menu of narrow ones. If a human engineer cannot say which
tool applies in a given situation, the model cannot be expected to do better. Tools should be self-contained,
robust to error, and unambiguous in their intended use, with descriptive parameter names that play to the
model’s strengths.
|              |           |                 |     |             | Rather | than loading all | potentially | relevant infor- |
| ------------ | --------- | --------------- | --- | ----------- | ------ | ---------------- | ----------- | --------------- |
| Just-in-time | retrieval | and progressive |     | disclosure. |        |                  |             |                 |
mation upfront, effective agents maintain lightweight identifiers such as file paths, stored queries, and web
links, and use them to load data on demand as the task unfolds. Anthropic Applied AI Team (2025) call
this approach disclosure. It mirrors how human experts work: we do not memorize corpora, we
progressive
build external indexing systems and retrieve on demand. Claude Code uses a hybrid strategy in practice.
CLAUDE.mdfilesareloadedatsessionstarttoprovideprojectcontext,whileglobandgrepcommandsletthe
agentnavigateandloadspecificfilecontentsjustintime. Thissidestepsboththestale-indexingproblemand
thecostoflargeprefills. Environmentalmetadataalsocarriesimplicitsignals. Filesizessuggestcomplexity;
naming conventions hint at purpose; timestamps proxy for relevance. Agents can assemble understanding
layer by layer, keeping only what is currently necessary in the active window.
|                |         |         | Prompt | caching | is the single | most cost-effective | optimization | available |
| -------------- | ------- | ------- | ------ | ------- | ------------- | ------------------- | ------------ | --------- |
| KV-cache-aware | context | design. |        |         |               |                     |              |           |
to production agent deployments, and its benefit depends entirely on how context is structured. After
five architectural iterations of their production agent, the Manus team identified KV-cache hit rate as “the
single most important metric for a production-stage AI agent,” noting that cached tokens on Claude Sonnet
cost $0.30/MTok compared to $3.00/MTok for uncached tokens (Manus Team, 2025). Three design rules
follow from the caching model. First, keep the prompt prefix stable: a single token difference at the start
of the system prompt invalidates the cache for everything that follows. Second, treat context as append-
only: modifying past actions or observations breaks cache reuse by creating a different prefix sequence.
Third, use deterministic serialization: non-stable key ordering in JSON serialization silently invalidates
caches across otherwise identical requests. Because tool definitions typically appear near the front of the
serialized context, adding or removing tools invalidates cached content for all subsequent turns. Manus
addresses this by using a context-aware state machine that masks token logits during decoding to prevent
selection of unavailable actions, rather than modifying the tool definition list at runtime (Manus Team,
2025). Anthropic’scontextmanagementreleaseoperationalizescachingattheproductlevelthroughexplicit
| cache_control | breakpoints | (Anthropic, |     | 2025c). |     |     |     |     |
| ------------- | ----------- | ----------- | --- | ------- | --- | --- | --- | --- |
The tooling ecosystem for short-term management has grown to include production skill libraries covering
KV-cache compaction patterns between agent calls (Koylan, 2025) and infrastructure projects providing
| MCP-centric   | primitives | for dynamic | context   | assembly    | (context-space, | 2025). |     |     |
| ------------- | ---------- | ----------- | --------- | ----------- | --------------- | ------ | --- | --- |
| 5.4 Mid-Term: | Session    | State and   | Cross-Run | Persistence |                 |        |     |     |
Mid-term context management addresses the gap between the active context window and a full long-term
memory system. The specific problem is how an agent preserves and restores state across turns within a
session, or across multiple runs of the same task. The engineering value is high: a few hundred tokens
of structured working state can bridge context resets that would otherwise cause the agent to lose all
| accumulated | progress. |     |     |     |     |     |     |     |
| ----------- | --------- | --- | --- | --- | --- | --- | --- | --- |
The simplest mid-term technique has the agent maintain a persistent notes file,
| Structured | note-taking. |     |     |     |     |     |     |     |
| ---------- | ------------ | --- | --- | --- | --- | --- | --- | --- |
typically a NOTES.md or todo.md, reading it at the start of each run and updating it before the context is
cleared. Anthropic Applied AI Team (2025) illustrate this through Claude playing Pokémon over thousands
of game steps. Without any explicit instruction about memory structure, the agent developed maps of
explored regions, maintained tallies of combat strategies and their outcomes against specific opponents, and
tracked objectives across context resets. After each compaction step that cleared the main conversation
history, the agent read its own notes and continued multi-hour training sequences without losing coherence.
Thekeyinsightisthatnote-takingexternalizesworkingmemory. Ratherthanrelyingonconversationhistory
to carry task state, the agent writes what matters to an external store and reads it back on demand.
|            |          |          |                  |     | An extension | of structured | note-taking | externalizes |
| ---------- | -------- | -------- | ---------------- | --- | ------------ | ------------- | ----------- | ------------ |
| File-based | planning | and task | externalization. |     |              |               |             |              |
the full planning representation to disk. Tools such as planning-with-files (OthmanAdi, 2025) provide skill
packages for persistent file-based planning within coding-agent workflows. Task state, specifications, inter-
21

Under review as submission to TMLR
mediateresults,anddependencygraphsarewrittentothefilesystemateachmilestoneandloadedselectively
at the start of the next run, bypassing the context window entirely for content that is not immediately rel-
evant. Frameworks such as Trellis (mindfold-ai, 2025) extend this pattern to include project memory and
spec injection, managing structured project state that is injected selectively based on what the current step
requires.
Cross-run injection. A complementary pattern captures the salient output of a prior run and injects it
at the start of the next. Tools such as claude-mem (thedotmack, 2025) operate as plugin-style memory
layers: they capture session history, extract the information most useful in a future run, and prepend it to
the next session’s context. This requires no vector database and no graph store, while providing substantial
continuity across runs. The community repository everything-claude-code (affaan-m, 2025), with over 150K
GitHub stars, represents the largest open collection of these patterns and demonstrates the scale at which
mid-tier memory practices have been adopted in production coding-agent deployments.
The mid-tier trade-off. Mid-term techniques provide significantly more continuity than in-window man-
agement alone, at a fraction of the infrastructure cost of full long-term memory systems. The limitation is
that information flows forward from one run to the next but is not retrieved from an indexed store, and
these techniques do not scale well to large volumes of history. When cross-run history grows large, or when
the agent needs to retrieve a specific prior observation rather than inject a summary, mid-term techniques
must be supplemented with the long-term systems described next.
5.5 Long-Term: Persistent Memory Systems
Long-term memory systems provide indexed, retrievable storage that persists across sessions, tasks, and
agent instances. Where mid-term techniques rely on forward injection of summaries, long-term systems
support arbitrary recall: given a query, the system retrieves the most relevant stored memories regardless of
when they were created. This tier is where the agent’s experience accumulates over time.
5.5.1 Foundational Architectures
OS-inspired tiered memory. Packer et al. (2023) introduced the key abstraction by treating the LLM’s
context window as RAM and external storage as disk, giving the model function calls that let it explicitly
page information in and out. The analogy to virtual memory is precise: just as an OS provides applications
the illusion of a larger memory through transparent paging, MemGPT provides the LLM the illusion of a
longer context through transparent memory management. Agents can operate on contexts that far exceed
the physical window limit, retrieving relevant history from external storage on demand. This paper made
explicit the connection between agent memory and OS memory that underlies most subsequent long-term
memory systems.
Observation, reflection, and retrieval. Parketal.(2023)introducedtheMemoryStreamarchitecturein
thecontextofsocialsimulationagents. TheMemoryStreamstoresalloftheagent’sobservationsasnatural-
language records with timestamps and importance scores. At each step, a retrieval model surfaces the most
relevant memories by combining three signals: recency, importance (scored by the agent at write time), and
relevance to the current query. A second mechanism, reflection, periodically synthesizes stored observations
intohigher-levelinsights. Theagentasksitselfwhatthemostsalientquestionsarefromitsrecentexperience,
retrievesrelevantrecords,andgeneratesconclusionsthatarestoredbackintotheMemoryStream. Ablation
experiments showed that each of the three components, observation, reflection, and retrieval, contributes
independently to behavior quality; removing any one produces measurable degradation. The observation-
reflection-retrieval triad remains the standard template for agent memory design.
Dynamic forgetting and personality modeling. Zhong et al. (2024) built MemoryBank on top of
the retrieval architecture with two additions. The first is a dynamic forgetting mechanism inspired by
the Ebbinghaus Forgetting Curve: memories decay over time according to an exponential model, frequent
accessstrengthensthem,andcontradictedmemoriesareresolved. Thesecondishierarchicaluser-personality
summaries, updated daily as new interactions accumulate. These ideas, adaptive memory strength and user
modeling, were later operationalized at scale in Mem0 and Honcho.
22

| Under review |            | as submission | to       | TMLR      |     |      |           |     |            |     |          |        |          |
| ------------ | ---------- | ------------- | -------- | --------- | --- | ---- | --------- | --- | ---------- | --- | -------- | ------ | -------- |
| 5.5.2        | Production | Memory        |          | Systems   |     |      |           |     |            |     |          |        |          |
|              |            |               |          |           |     | Mem0 | (Chhikara | et  | al., 2025) | is  | the most | widely | deployed |
| Hybrid       | storage    | and           | industry | adoption. |     |      |           |     |            |     |          |        |          |
long-term memory layer for production agents at present, with over 14 million Python package downloads,
41K GitHub stars, and native integration in CrewAI, Flowise, and Langflow. Its architecture combines
three storage backends: a vector database for semantic similarity search, a graph database for relationship
modeling, and a key-value store for fast fact retrieval. An LLM-based extraction layer processes new in-
teractions, identifies facts and preferences, and routes records to the appropriate store. On the LOCOMO
benchmark,Mem0achieves26%higheraccuracythanOpenAI’snativememorywhileusing90%fewertokens
than a full-context approach (Chhikara et al., 2025). Amazon Web Services selected Mem0 as the exclusive
memory provider for its Agent SDK in 2025, reflecting its transition from research prototype to production
infrastructure.
|         |           |     |           |     | A-MEM | (Xu et | al., 2025) | draws | on  | the Zettelkasten |     | knowledge | man- |
| ------- | --------- | --- | --------- | --- | ----- | ------ | ---------- | ----- | --- | ---------------- | --- | --------- | ---- |
| Dynamic | knowledge |     | networks. |     |       |        |            |       |     |                  |     |           |      |
agement system. Rather than storing memories as flat records, it generates a structured note for each new
memory that includes keywords, tags, a contextual description, and a dynamic set of links to semantically
related memories. When a new memory is added, A-MEM not only stores it but also retroactively updates
the context and attributes of existing related notes, allowing the memory graph to evolve as knowledge ac-
cretes. Thisaddressesafundamentallimitationofretrieval-basedsystems: therelevanceofastoredmemory
may not be apparent at write time, and its significance can only be assessed in relation to later information.
|          |      |             |     | Hindsight |     | (Vectorize.io, | 2025) | takes | the | position | that | most memory | sys- |
| -------- | ---- | ----------- | --- | --------- | --- | -------------- | ----- | ----- | --- | -------- | ---- | ----------- | ---- |
| Learning | from | experience. |     |           |     |                |       |       |     |          |      |             |      |
tems focus on remembering when the real need is learning. Its API exposes three operations: retain to
store new information, to retrieve relevant memories, and to generate a disposition-aware
|     |     |     | recall |     |     |     |     |     | reflect |     |     |     |     |
| --- | --- | --- | ------ | --- | --- | --- | --- | --- | ------- | --- | --- | --- | --- |
response that integrates memory with current context. Internally, the retain operation extracts temporal
entities,deduplicatesoverlappingfacts,andbuildsevidence-groundedconsolidatedknowledgerecords. Hind-
sight achieves state-of-the-art performance on the LongMemEval benchmark, independently reproduced by
| researchers      | at  | the Virginia     | Tech | Sanghani | Center. |          |       |        |           |     |            |       |          |
| ---------------- | --- | ---------------- | ---- | -------- | ------- | -------- | ----- | ------ | --------- | --- | ---------- | ----- | -------- |
|                  |     |                  |      |          | Honcho  | (Plastic | Labs, | 2025), | developed |     | by Plastic | Labs, | builds a |
| Reasoning-driven |     | personalization. |      |          |         |          |       |        |           |     |            |       |          |
model ofusersratherthanastoreoffactsaboutthem. Anasynchronousreasoningpipelinecalled“dreaming”
continuously processes past interactions in the background, extracting not just explicit facts but inferred
conclusions about preferences, communication styles, and evolving goals. The entity-centric data model
supportsmulti-agentenvironmentswheremultipleagentsinteractwiththesameuser: eachagentmaintains
its own observation perspective, preventing cross-contamination while a shared user model accumulates
| understanding |     | from all | interactions. |     |     |     |     |     |     |     |     |     |     |
| ------------- | --- | -------- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
MozillaAI’scq(MozillaAI,2025)addressesagapthattheothersystemsleaveopen:
| Collective | memory. |     |     |     |     |     |     |     |     |     |     |     |     |
| ---------- | ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
shared memory across agent instances. Most long-term memory systems are per-agent or per-user; when
multiple agents work on related tasks, each instance independently rediscovers what the others have already
learned. cqisanopenstandardforsharedagentlearninginwhichagentspersist,query,andconfirmcollective
knowledge across a fleet. Its architecture is MCP-native and operates at three tiers: local knowledge stored
on the developer’s machine, organization-shared knowledge accessible to a team, and cross-team knowledge.
The post-error hook pattern, where cq automatically queries the collective knowledge base when an agent
encountersanerror,providesaconcretemechanismforpreventingrepeatedfailuresfrombeingindependently
| resolved | across   | an organization’s |     | deployments. |     |     |     |     |     |     |     |     |     |
| -------- | -------- | ----------------- | --- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5.5.3    | Academic | Surveys           | and | Taxonomy     |     |     |     |     |     |     |     |     |     |
The memory mechanism survey by Zhang et al. (2025) provides the standard academic taxonomy for this
layer. It distinguishes short-term working memory from long-term memory, and subdivides the latter into
semantic, procedural, and episodic categories. The write-read-manage loop it formalizes has become the
standard vocabulary for describing memory system behavior. A more recent survey (Du, 2026) builds on
thisbyformalizingtheloopwithinaPOMDP-styleagentcycleandproposingathree-dimensionaltaxonomy
covering memory scope, storage format, and compositional structure. It characterizes three engineering
patterns: Pattern A (monolithic context), Pattern B (context window plus retrieval store), and Pattern C
(tiered memory with learned control policies). These correspond roughly to the short-term, mid-term,
23

Under review as submission to TMLR
and long-term tiers described in this section. The RAG survey by Gao et al. (2023) provides background on
retrieval-augmentedgenerationthatunderpinstheretrievaltieroftheproductionmemorysystemsdescribed
above.
5.6 Long-Horizon Techniques: Keeping Agents Coherent Over 100+ Turns
Each of the preceding sections addresses a single time horizon. Long-horizon tasks, including large codebase
migrations, multi-session research projects, and extended autonomous workflows, require coordinating all
three tiers simultaneously and making real-time decisions about which technique to apply at each point.
This section covers the integration-level techniques that emerge at this scale.
Context compaction. Compaction summarizes a context window approaching its limit and reinitiates
execution with a compressed representation of the accumulated state. Anthropic Applied AI Team (2025)
describe the calibration challenge in detail. The summary must preserve architectural decisions, unresolved
bugs,andimplementationdetailswhilediscardingredundanttooloutputsandintermediatereasoningalready
incorporatedintolatersteps. Therecommendedtuningworkflowstartsbymaximizingrecall,capturingevery
potentially relevant piece of information from the trace, then iterates to improve precision by removing
superfluous content. One does not start from the other direction. Removing too much early produces an
agent that loses context it needed later, and that loss is not recoverable. Tool result clearing is the lightest
form of compaction: full tool outputs are replaced with compact path references once the agent has acted
on them. This can be applied continuously and is now a product-level feature on the Anthropic developer
platform (Anthropic, 2025c).
Sub-agent context isolation. When a task requires deep exploration of a subtopic, the exploration
itself generates large amounts of intermediate context that is useful within the subtask but pollutes the
orchestrator’s view of the overall task. The sub-agent architecture addresses this by assigning subtasks to
dedicated agents, each with a fresh context window, which return only a condensed 1,000 to 2,000 token
summary of their findings to the orchestrator (Anthropic, 2025e). The detailed exploration context stays
isolatedwithinthesub-agent;theorchestratorreceivesonlythedistilledresult. ManusTeam(2025)describe
arefinementofthispattern. Forsimplesubtaskswheretheorchestratorneedsonlytheoutput,contextisnot
shared at all. For complex subtasks where shared state is required, the orchestrator’s full context is passed
tothesub-agent. Sharingcontextbetweenagentsisexpensive: itproduceslargerprefillsandeliminatesKV-
cache reuse across different system prompts. The trade-off between isolation cost and coordination benefit
must be made explicitly for each task type.
Hybrid decision frameworks. Production deployments do not apply a single technique uniformly; they
select different techniques at different points in the execution based on task structure. Anthropic (2026c)
characterize the framework as: pre-load content that is always needed, retrieve just-in-time content that
is conditionally needed, compact history when the window approaches saturation, and spawn sub-agents
when a subtask requires exploration that would pollute the orchestrator’s context. Anthropic (2025d) add
the harness-level perspective: checkpoint and resume patterns allow agents to survive transient failures
withoutlosingtaskstate,andlifecyclehookscantriggercompactionormemoryconsolidationautomatically
at configurable thresholds. This is the right division of responsibility. Context management should be the
infrastructure’sjob,nottheagent’s. Whentheharnesshandlescompactionandconsolidationautomatically,
the model can focus on task reasoning.
5.7 Context Drift and the Limits of Current Approaches
The binding-constraint view frames context drift as a controller-side failure mode: because the model only
sees the projection of state exposed by the harness, loss or distortion of task-relevant context is a harness
property rather than a model property alone (Bölük, 2026b). All of the techniques described above work, in
varying degrees, under varying conditions. None of them solves the underlying problem. Context drift, the
progressive degradation of agent behavior over extended interactions, remains the hardest open challenge in
this layer.
24

| Under review | as  | submission | to       | TMLR    |       |     |               |         |      |        |                     |
| ------------ | --- | ---------- | -------- | ------- | ----- | --- | ------------- | ------- | ---- | ------ | ------------------- |
|              |     |            |          | Context | drift | is  | distinct from | context | rot, | though | both arise from the |
| The nature   | of  | the        | problem. |         |       |     |               |         |      |        |                     |
same architectural constraints. Context rot (Section 5.1) is a property of a single inference step: adding
more tokens to a fixed context degrades retrieval and reasoning quality. Context drift is a property of an
extended trajectory. As the agent accumulates turns, its behavior drifts from the original intent in ways
that compaction and retrieval steps can slow but not prevent. After 100 or more turns, agents frequently
repeat work already done, contradict earlier decisions without awareness, and lose track of the motivating
goal (Bowne-Anderson & Huber, 2026). The root cause is not simply window saturation. Even with aggres-
sivecompaction,thesummariesthatsurviveeachcompressionstepcarrysubtleinaccuraciesthatcompound
overtime. Theagent’saccumulatedassumptionscandivergefromtheactualtaskenvironment,andnothing
| in the current | architecture |     | detects | this | divergence. |     |     |     |     |     |     |
| -------------- | ------------ | --- | ------- | ---- | ----------- | --- | --- | --- | --- | --- | --- |
A secondary problem is that context drift is hard to measure. Standard benchmarks
| The evaluation |     | gap. |     |     |     |     |     |     |     |     |     |
| -------------- | --- | ---- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
evaluate agents on tasks that complete within a few dozen steps; the failure modes that appear at 100
or more turns are not captured. Recent work has begun to close this gap. Tan et al. (2025) introduce
MemBench, which evaluates memory quality across multi-session scenarios including temporal reasoning,
knowledge update, and cross-session aggregation. He et al. (2026) introduce MemoryArena specifically
for interdependent multi-session tasks, the conditions under which context drift is most destructive. Hu
et al. (2025b) propose an incremental multi-turn evaluation methodology that isolates memory quality from
generation quality. These benchmarks are necessary but not sufficient. They show that drift occurs, but
| they do     | not yet | provide    | the mechanistic |        | understanding |     | needed  | to prevent | it.   |     |                       |
| ----------- | ------- | ---------- | --------------- | ------ | ------------- | --- | ------- | ---------- | ----- | --- | --------------------- |
|             |         |            |                 |        | Compaction    |     | reduces | the token  | count | but | cannot guarantee that |
| Why current |         | techniques | fall            | short. |               |     |         |            |       |     |                       |
the compressed representation accurately captures all relevant state. Information lost at each compression
step is gone. Retrieval systems can surface relevant prior memories, but the query must be well-formed to
do so. A drifting agent may not know what it needs to retrieve to correct its course. Sub-agent isolation
prevents subtask context from polluting the orchestrator, but the orchestrator’s own context still accumu-
lates drift over time. Bowne-Anderson & Huber (2026) argue that these limitations point to a boundary:
context engineering alone cannot solve long-horizon reliability. A full harness layer with verification loops,
human-in-the-loop checkpoints at strategic intervals, and anomaly detection capable of identifying behav-
ioral divergence is required. This motivates the governance and observability layers discussed in Sections 7
and 9 as necessary complements to context engineering, not separate concerns.
| 6 Lifecycle |     | and Orchestration |              |     | (L)      |                 |                               |                            |                    |                      |                        |
| ----------- | --- | ----------------- | ------------ | --- | -------- | --------------- | ----------------------------- | -------------------------- | ------------------ | -------------------- | ---------------------- |
|             |     |                   |              |     | R e A c  | t ( Y a o e t a | l ., 2 0 2 3 ) , C o d e x    | A g e n t L o o p ( O p    | e n A I , 2 0 2 6  | b ) ,                |                        |
|             |     | S i n g           | le -A g en t |     |          |                 |                               |                            |                    |                      |                        |
|             |     | I n n             | e r Lo o p   |     | O p en   | C o d e ( A n o | m a l y , 2 0 2 5 ) , C l a   | u d e C o d e ( A n t h    | r o p ic , 2 0 2 5 | ) , G e m in i C L I | ( G o o g l e , 2025), |
|             |     |                   |              |     | Co d e x | C L I ( O p     | e n A I , 2 0 2 5 ) , A i d e | r ( A i d e r - A I, 2 0 2 | 5 ) , S W E - A    | g e n t (S W E - a   | ge n t , 2 0 2 5 )     |
&elcycefiL noitartsehcrO
AnthropicMulti-AgentResearchSystem(Anthropic,2025e),
|     |     | M u lt | i - A g en t |     | H a r n e | s s D e s i g n | ( A n th r o p i c , 2 0 2 6  | c ) , A u t o G e n ( M   | i c r o s o f t , 2 0 | 2 5 ) , D e e r F lo w | ( B y t e da n ce , 2 0 2 6 ) , |
| --- | --- | ------ | ------------ | --- | --------- | --------------- | ----------------------------- | ------------------------- | --------------------- | ---------------------- | ------------------------------- |
|     |     |        |              |     | L a n g G | r a ph ( L a    | n g C h a i n , 2 0 2 6 a ) , | S e m a n t i c K e r n e | l ( M i c r o s o ft  | , 2 0 2 6 ) ,          |                                 |
Orche st ra t i o n P a tterns O p e n A I A g e n t s S D K ( O p e n A I , 2 0 2 6 a ) , D ee p A g e n t s ( L a n g C h a in , 2 0 2 6 b ) ,H i v e ( A d en , 2 0 2 6 ) ,
Emdash(Action,2026)
TaskRunners(OpenAI,2026a;LangChain,2026b),
|     |                        | FullLifecyclePipeline |     |     | EffectiveHarnesses(Anthropic,2025d),              |     |     |     |     |     |     |
| --- | ---------------------- | --------------------- | --- | --- | ------------------------------------------------- | --- | --- | --- | --- | --- | --- |
|     | fromIssuetoPullRequest |                       |     |     | VibeKanban(Bloop-AI,2026),Symphony(OpenAI,2026b), |     |     |     |     |     |     |
GitHubAgenticWorkflows(GitHub,2026)
Figure 9: Representative work on lifecycle and orchestration for LLM agents, organized by the chapter’s
| orchestration | categories. |     |     |     |     |     |     |     |     |     |     |
| ------------- | ----------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Lifecycle and Orchestration (L) concerns how an agent system carries a task across repeated model calls,
tool calls, failures, revisions, and handoffs. This layer combines two concerns that are often separated in
earlier frameworks: the execution flow of the agent and the operational state that the flow reads and writes.
In long-running tasks, reliability depends not only on whether the model can produce a good next action,
butalsoonwhethertheharnesscanrememberwhathasalreadyhappened,decidewhatshouldhappennext,
recover from errors, coordinate subtasks, and stop when the task is complete (OpenAI, 2026b; Anthropic,
2025d; 2026c). We therefore treat Lifecycle and Orchestration as the fourth pillar of ETCLOVG (Claim 2
in §1), drawing examples from the corpus of over 100 projects that supports Claim 3 in §1.
25

| Under | review as submission | to TMLR |     |     |     |     |
| ----- | -------------------- | ------- | --- | --- | --- | --- |
Table 2: Representative orchestration systems, organized by orchestration level (single-agent: § 6.2, multi-
agent: § 6.3, full lifecycle pipeline: § 6.4), primary orchestration pattern, and execution model. GitHub
| stars are | rounded to | the nearest thousand | and recorded | as of May 12, 2026. |     |     |
| --------- | ---------- | -------------------- | ------------ | ------------------- | --- | --- |
SystemorFramework GitHubURL GitHubStars(k) Section PrimaryPattern ExecutionModel
Single-AgentInnerLoop
| OpenCode(Anomaly,2025) |     |     |     | 159 6.2 | Singleloop | Hybrid |
| ---------------------- | --- | --- | --- | ------- | ---------- | ------ |
anomalyco/opencode
| ClaudeCode(Anthropic,2025) |     |     |     | 123 6.2 | Singleloop | Hybrid |
| -------------------------- | --- | --- | --- | ------- | ---------- | ------ |
anthropics/claude-code
| GeminiCLI(Google,2025) |     |     |     | 104 6.2 | Singleloop | Hybrid |
| ---------------------- | --- | --- | --- | ------- | ---------- | ------ |
google-gemini/gemini-cli
| CodexCLI(OpenAI,2025) |     |     |     | 82 6.2 | Singleloop | Statelessreplay |
| --------------------- | --- | --- | --- | ------ | ---------- | --------------- |
openai/codex
| Aider(Aider-AI,2025) |     |     |     | 45 6.2 | Singleloop | Hybrid |
| -------------------- | --- | --- | --- | ------ | ---------- | ------ |
aider-ai/aider
| SWE-agent(SWE-agent,2025) |     |     |     | 19 6.2 | Singleloop | Hybrid |
| ------------------------- | --- | --- | --- | ------ | ---------- | ------ |
swe-agent/swe-agent
Multi-AgentOrchestrationPatterns
DeerFlow(Bytedance,2026) 67 6.3 Hierarchicalorchestration Stateful
bytedance/deer-flow
AutoGen(Microsoft,2025) 58 6.3 Hierarchicalorchestration Stateful
microsoft/autogen
| oh-my-claudecode(Heo,2026) |     |     |     | 34 6.3 | Teamorchestration | Stateful |
| -------------------------- | --- | --- | --- | ------ | ----------------- | -------- |
yeachan-heo/oh-my-claudecode
| LangGraph(LangChain,2026a) |     |     |     | 32 6.3 | Graphcomposition | Stateful |
| -------------------------- | --- | --- | --- | ------ | ---------------- | -------- |
langchain-ai/langgraph
SemanticKernel(Microsoft,2026) 28 6.3 Workfloworchestration Stateful
microsoft/semantic-kernel
OpenAIAgentsSDK(OpenAI,2026a) openai/openai-agents-python 26 6.3 Hierarchicalorchestration Hybrid
DeepAgents(LangChain,2026b) langchain-ai/deepagents 23 6.3 Hierarchicalorchestration Stateful
Hive(Aden,2026) aden-hive/hive 10 6.3 Graphcomposition Stateful
Emdash(Action,2026) generalaction/emdash 4 6.3 Fan-out Hybrid
FullLifecyclePipelinefromIssuetoPullRequest
VibeKanban(Bloop-AI,2026) BloopAI/vibe-kanban 26 6.4 Fulllifecyclepipeline Stateful
Symphony(OpenAI,2026b) openai/symphony 24 6.4 Fulllifecyclepipeline Stateful
GitHubAgenticWorkflows(GitHub,2026) github/gh-aw 5 6.4 Fulllifecyclepipeline Hybrid
Thislayerspansthreelevelsoforganization. Asingle-agent loopistherepeatedcycleinwhichone
inner
agent observes the current situation, decides on an action, invokes a tool or produces an output, and uses
the result to continue. Multi-agent orchestration coordinates several such loops, usually by assigning
different roles to different agents or by routing work among them. A places these
full lifecycle pipeline
agent loops inside a broader software or task workflow, such as moving from an issue to code changes, tests,
review, and a pull request. Across these levels, systems also differ in how they maintain state.
Stateless
replay reconstructs the run from the recorded interaction history. Stateful execution stores operational state
outside the prompt, for example in files, repositories, databases, task graphs, or services. Many practical
systems are hybrid: they keep replayable histories while also relying on persistent artifacts.
| 6.1 Lifecycle | State | Management |     |     |     |     |
| ------------- | ----- | ---------- | --- | --- | --- | --- |
Lifecyclestatemanagementconcernstheoperationalstateneededtocontinueanagentrunacrossturns,ses-
sions, failures, and handoffs. This includes pending subtasks, tool results, intermediate artifacts, repository
changes,coordinationmetadata,sessionpersistence,andcheckpointresumemechanisms. Thesemechanisms
makeorchestrationdurableratherthantransient: theagentcancontinuefrompriorworkinsteadoftreating
| every step | as an isolated | model call. |     |     |     |     |
| ---------- | -------------- | ----------- | --- | --- | --- | --- |
A central trade-off is between stateless and stateful execution. Stateless designs reconstruct execution from
prior interaction history, improving reproducibility and auditability but becoming costly as trajectories
grow. Stateful designs persist execution state in files, databases, repositories, task graphs, or external
services, improving continuity and recovery but introducing consistency and debugging challenges (OpenAI,
2026b; Anthropic, 2026c). Many practical harnesses therefore adopt hybrid designs, combining replayable
| interaction | histories with | persistent artifacts. |     |     |     |     |
| ----------- | -------------- | --------------------- | --- | --- | --- | --- |
This state is distinct from the Context and Memory layer in §5, which concerns the information provided to
the model for reasoning, such as retrieved documents, memories, or conversation history. It is also distinct
from Observability in §7, which concerns logging, tracing, and monitoring system behavior. Here, the focus
26

Under review as submission to TMLR
is instead on the operational state used by the harness itself to continue and coordinate execution, such as
pending subtasks, checkpoints, retries, shared artifacts, or execution status.
6.2 Single-Agent Inner Loop
The single-agent inner loop is the basic execution unit in agent systems. A single agent repeatedly interacts
with an environment through tool use and feedback, without explicit coordination among multiple agents.
This abstraction underlies interactive coding, debugging, and problem solving.
Conceptually, the single-agent loop follows the ReAct paradigm (Yao et al., 2023), interleaving reasoning,
action, and observation. As emphasized in OpenAI’s analysis of the Codex agent loop (OpenAI, 2026b),
the behavior of such a system is determined not only by the model, but also by the harness that constructs
prompts, invokes tools, manages control flow, and feeds tool outputs back into later steps.
At this level, the main execution distinction is between Stateless replay and Hybrid execution. Codex
CLI (OpenAI, 2025) is the clearest example of replay-based execution, while practical coding agents often
combine replayable histories with persistent artifacts such as files, repositories, or session state. In Table 2,
OpenCode(Anomaly,2025),ClaudeCode(Anthropic,2025),GeminiCLI(Google,2025),CodexCLI(Ope-
nAI, 2025), Aider (Aider-AI, 2025), and SWE-agent (SWE-agent, 2025) are therefore grouped under the
primary pattern Single loop. Despite their flexibility, long-horizon execution in such systems can suffer from
context fragmentation, accumulated errors, and weak decomposition structure (Anthropic, 2025d), motivat-
ing more structured orchestration.
6.3 Multi-Agent Orchestration Patterns
Multi-agentorchestrationextendsthesingle-agentloopbycomposingmultipleagentswithspecializedroles.
Insteadofaskingoneagenttoplan,execute,check,andrevisealone,amulti-agentharnesscanseparatethese
responsibilitiesacrossagentsorsubagents. Thisstructuresupportstaskdecomposition,parallelexploration,
critique, validation, and aggregation, making it better suited to complex tasks than an isolated loop.
Several recurring patterns appear in this design space. Hierarchical orchestration uses a higher-level con-
troller to assign work to agents or subagents and integrate their outputs. Team orchestration exposes a
collection of specialized agents as a coordinated team, usually with different named responsibilities. Work-
flow orchestration organizes agents and tools into explicit stages or control logic. Fan-out runs multiple
agentsinparalleltoexplorediversesolutions. Graph composition representsagents,tools,orstatesasnodes
in an interaction graph, allowing multiple coordination patterns to coexist. These labels match the primary
pattern categories used in Table 2.
Execution at this level is usually Stateful or Hybrid, since multi-agent systems must maintain coordina-
tion state, role assignments, task graphs, shared artifacts, or intermediate results. Anthropic’s planner-
generator-evaluator architecture (Anthropic, 2025e) illustrates the broader principle: planning, execution,
andverificationcanbeseparatedintoexplicitroles,improvingdecompositionandrobustnesswhileincreasing
coordination overhead (Anthropic, 2026c).
The systems in Table 2 instantiate these patterns in different ways. DeerFlow (Bytedance, 2026), Auto-
Gen (Microsoft, 2025), OpenAI Agents SDK (OpenAI, 2026a), and DeepAgents (LangChain, 2026b) are
classified as Hierarchical orchestration. oh-my-claudecode (Heo, 2026) is classified as Team orchestration.
LangGraph (LangChain, 2026a) and Hive (Aden, 2026) exemplify Graph composition, Semantic Kernel (Mi-
crosoft, 2026) exemplifies Workflow orchestration, and Emdash (Action, 2026) exemplifies Fan-out.
6.4 Full Lifecycle Pipeline from Issue to Pull Request
Full lifecycle orchestration manages an entire task workflow from specification to validated output. At this
level, the focus is not only on how agents interact, but on how a harness supports long-horizon execution
across planning, implementation, validation, review, and delivery.
27

| Under review | as  | submission | to TMLR |     |     |     |     |     |     |
| ------------ | --- | ---------- | ------- | --- | --- | --- | --- | --- | --- |
The central abstraction is the runner: a harness that manages scheduling, state persistence, retries,
task
validation, and iterative refinement over a complete task lifecycle (OpenAI, 2026a; LangChain, 2026b).
Execution is grounded in persistent artifacts such as repositories, issues, branches, files, tests, and pull
requests. A canonical workflow proceeds from an issue or task specification through agent planning, code or
artifact generation, validation, human review, and eventual pull request acceptance.
Because these systems operate over persistent repositories and external workflows, the dominant execution
model is usually Stateful. Some systems combine persistent infrastructure state with replay-like or session-
local execution inside subcomponents, motivating the label in Table 2. Vibe Kanban (Bloop-AI,
Hybrid
2026), Symphony (OpenAI, 2026b), and GitHub Agentic Workflows (GitHub, 2026) are classified as Full
lifecycle pipeline. Conceptually,thesesystemscomposethepreviousabstractions: single-agentloopsprovide
theexecutionprimitive,multi-agentpatternsprovidecoordination,andthetaskrunnerintegratestheminto
| an end-to-end   | workflow |     | in which humans | steer | while agents | execute. |     |     |     |
| --------------- | -------- | --- | --------------- | ----- | ------------ | -------- | --- | --- | --- |
| 7 Observability |          | and | Operations      | (O)   |              |          |     |     |     |
ObservabilityandOperations(O)isthefifthlayerofETCLOVGandthefirstofthetwolayersourtaxonomy
promotes from Lifecycle Hooks to first-class status (Claim 2 in §1). The supporting systems are drawn from
| the 170+ | project | corpus | that backs Claim | 3.        |                                   |                                             |                                   |                               |               |
| -------- | ------- | ------ | ---------------- | --------- | --------------------------------- | ------------------------------------------- | --------------------------------- | ----------------------------- | ------------- |
|          |         |        |                  | L a n g f | u s e ( L a n g f u s e , 2 0 2 6 | ) , O p i k ( C o m e t M L , 2 0 2 6 ) , P | h o e n i x ( A r i z e A I , 2 0 | 26 b ), M L fl ow ( M L fl ow | , 2 0 2 6 ) , |
T r a c in g a n d O p e n T e l e m e t r y ( O p e n T e l e m e t r y , 2 0 2 6 ) , O p en L L M e tr y ( T r a c e l o o p , 20 2 6 ) , O p en In fe r en ce ( A ri ze A I , 2 0 2 6 a),
|     |     | Moni to r i n g | P la t forms |         |                                   |                                                  |                         |     |     |
| --- | --- | --------------- | ------------ | ------- | --------------------------------- | ------------------------------------------------ | ----------------------- | --- | --- |
|     |     |                 |              | A g e n | t S i g h t ( Z h e n g e t a l . | , 2 0 2 5 ) , A g e n t T r a c e ( A lS a y y a | d e t a l . , 2 0 2 6 ) |     |     |
A g e n t - Sp e ci fi c A g e n t O p s ( A g e n t O p s A I , 2 0 2 6 ) , R a g a A I C a t a lys t ( R a g a A I, 2026),Laminar(LaminarAI,2026),
|                |     | Ope ra t i o n | s P la t fo rms | W a t s  | o n ( R o m b a u t e t a l . ,  | 2 0 2 5 ) , A g e n t L en s ( L u e t a l. , | 2 0 24 ), |     |     |
| -------------- | --- | -------------- | --------------- | -------- | -------------------------------- | --------------------------------------------- | --------- | --- | --- |
| &ytilibavresbO |     |                |                 | Cl a u d | e - C od e - R e v e r s e ( Y u | , 2 0 2 6 )                                   |           |     |     |
snoitarepO
|     |     | C o st T    | r ac k in g  | T e n s o | r Z e r o ( T en s o r Z e r o , | 2 02 6 ) , H e l i c o n e ( H e l ic o n e , 2 0 | 2 6 ) , F r u g alGPT(Chenetal.,2023), |     |     |
| --- | --- | ----------- | ------------ | --------- | -------------------------------- | ------------------------------------------------- | -------------------------------------- | --- | --- |
|     |     |             |              | G P T C   | a c h e ( B a n g , 2 0 2 3 )    | , Q C - O p t ( S h e k h a r e t a l . , 2 0 2   | 4 ),                                   |     |     |
|     |     | an d O p ti | m iz a ti on | T A L E   | ( H a n e t a l . , 2 0 2 5 ) ,  | D u a l -P o o l R o u t i n g ( L i u e t a      | l . , 2 0 2 6 b )                      |     |     |
EffectiveHarnesses(Anthropic,2025d),HarnessDesign(Anthropic,2026c),
|     |     | Reliability |     | ManagedAgents(Anthropic,2026b),MAST(Cemrietal.,2025),          |     |     |     |     |     |
| --- | --- | ----------- | --- | -------------------------------------------------------------- | --- | --- | --- | --- | --- |
|     |     | Engineering |     | AgentErrorTaxonomy(Zhuetal.,2025),SentinelAgent(Heetal.,2025), |     |     |     |     |     |
AgentFixer(Mulianetal.,2026),QSAF(Attaetal.,2025)
TamingUncertainty(Moshkovich&Zeltyn,2025),
|     |     | Unified       |     | BeyondBlack-BoxBenchmarking(Moshkovichetal.,2025),MindtheMetrics(Kocetal.,2025), |     |     |     |     |     |
| --- | --- | ------------- | --- | -------------------------------------------------------------------------------- | --- | --- | --- | --- | --- |
|     |     | Observability |     | NLAH(Panetal.,2026),Deep-AgentEvaluation(LangChain,2025a),                       |     |     |     |     |     |
InfrastructureNoise(Anthropic,2026a)
Figure 10: Representative work on observability and operations for LLM agents, organized by the chapter’s
| operational | categories. |     |     |     |     |     |     |     |     |
| ----------- | ----------- | --- | --- | --- | --- | --- | --- | --- | --- |
Thislayeraddresseshowagentbehaviorismonitored,debugged,andmadereliableinproduction. Weargue
that observability deserves independent treatment, separate from lifecycle hooks, because it has spawned a
| dedicated   | ecosystem | of platforms, | specifications, |     | and engineering | practices. |     |     |     |
| ----------- | --------- | ------------- | --------------- | --- | --------------- | ---------- | --- | --- | --- |
| 7.1 Tracing | and       | Monitoring    | Platforms       |     |                 |            |     |     |     |
Thefoundationofagentobservabilityisstructuredtracecollection: recordingeveryLLMcall,toolinvocation,
retrievalstep,andcontext-assemblyoperationasatreeofspansthatcanbeinspected,filtered,andreplayed.
Langfuse,Opik,ArizePhoenix,andMLfloweachofferinteractivetracetreeswithlatencyflamecharts,token-
usage breakdowns, cost attribution dashboards, and prompt versioning Langfuse (2026); Comet ML (2026);
Arize AI (2026b); MLflow (2026). These platforms typically ingest traces via lightweight SDK wrappers
(e.g., a decorator) that instrument the agent’s function calls with minimal code changes.
@traceable
Beneaththeseplatforms,OpenTelemetry(OTel)hasemergedasthedefactoinstrumentationstandard. The
OTelcommunityhaspublishedsemanticconventionsforgenerativeAIthatdefinespanattributesformodel
name,temperature,tokencounts,andlatencyOpenTelemetry(2026). Twoopen-sourceprojectsoperational-
ize these conventions: OpenLLMetry provides auto-instrumentation libraries for LLM providers (OpenAI,
Anthropic, Cohere) and vector databases (Pinecone, Chroma, Weaviate), emitting standard OTel spans and
metricsTraceloop(2026); OpenInference,maintainedbyArizeAI,offersacomplementaryspecificationwith
28

Under review as submission to TMLR
OTel-alignedsemanticconventionsandauto-instrumentationsdesignedasacompaniontoPhoenixArizeAI
(2026a). BybuildingonOTel, theselibrariesallowagenttracestoflowintothesameobservabilitybackends
(Prometheus, Jaeger, Grafana, Datadog) that teams already use for traditional microservice monitoring,
reducing the operational overhead of adopting agent-specific tooling.
At a deeper instrumentation level, academic work has explored techniques that go beyond application-level
decorators. AgentSightZhengetal.(2025)useseBPFtomonitoragentsfromoutsidetheapplicationprocess,
interceptingTLS-encryptedLLMtrafficattheSSLboundarytocaptureintent,andmonitoringkernelevents
(process creation, file I/O, network calls) to capture actions. A real-time correlation engine links LLM
responsestothesystembehaviorstheytrigger, andasecondary“observer”LLMperformssemanticanalysis
to identify risks. This approach is framework-agnostic, requires no code modifications, and incurs less
than 3% CPU overhead. The authors note a structural advantage over application-level tools: system-level
monitoring cannot be bypassed by a compromised or misconfigured agent, making it particularly relevant
for safety-critical deployments. AgentTrace AlSayyad et al. (2026) proposes a complementary schema-based
loggingframeworkthatcapturesstructuredlogsacrossthree“surfaces”: cognitivereasoningsteps,plans,and
reflections; operational tool calls and API interactions; and contextual environment state and user inputs.
These surfaces are organized under a unified envelope that integrates with OTel for export. The cognitive
surface is especially relevant to harness engineering because it captures explicit reasoning artifacts, plans,
reflections, and self-corrections. These records provide raw material for debugging failures that arise from
incorrect reasoning rather than system errors.
7.2 Agent-Specific Operations Platforms
General-purposetracingplatformsoftencentertheirabstractionsonLLMcalls,toolcalls,andretrievalsteps
as span-level events. Agent-specific platforms add a layer of abstraction that captures agent-level concerns:
multi-step session tracking, agent identity and role management, tool-selection policies, and cross-session
statehandoff. AgentOpsSDKintroducesahierarchicalspanmodelthatorganizessessions,agents,operations
ortasks,workflows,toolcalls,andLLMcallsaroundtheagentlifecycleratherthantreatingthemasisolated
API calls AgentOps AI (2026). RagaAI Catalyst targets RAG and multi-agent workloads with quality and
safety dashboards that surface retrieval-level and agent-level anomalies RagaAI (2026). Laminar offers an
OSS-first agent observability platform combining trace, evaluation, and prompt management Laminar AI
(2026).
The academic community has begun to formalize these concerns. Researchers Moshkovich & Zeltyn (2025)
proposeasix-stageAgentOpsautomationpipeline: observe, collectmetrics, detectanomalies, performroot-
cause analysis, recommend fixes, and automate remediation. They further decompose the stakeholder space
into four roles: developer, tester, SRE, and business user, each engaging with the pipeline at different
lifecycle points. Their companion empirical study Moshkovich et al. (2025) introduces task-flow discovery
as an observability primitive and demonstrates through user studies that 79% of practitioners identify non-
deterministic execution flow as the most significant challenge in agentic systems.
TheNatural-LanguageAgentHarnesses(NLAH)frameworkPanetal.(2026)withacompanionopen-source
implementation, takes the complementary step of treating the harness itself as a first-class research object.
Through systematic ablation experiments, the authors quantify how individual harness modules contribute
to downstream agent performance. These modules include the tool registry, permission system, hooks,
skills, and context folding. The implication for observability is that the harness is not merely the subject of
monitoring but a source of interventions: each module ablated is a knob that the observability pipeline can
flag and tune.
Cognitive observability extends agent-level monitoring to ask not just what an agent did, but why. Wat-
sonRombautetal.(2025)introducesthisconceptformally,deployinga“surrogateagent”thatreproducesthe
primary agent’s output while generating a step-by-step reasoning trace via prompt attribution. Evaluated
onMMLUandSWE-bench-litewithAutoCodeRoverandOpenHands, Watsondemonstratesthatrecovered
reasoning traces are useful both for manual debugging and for automated correction, yielding measurable
improvements in task success rates. AgentLens Lu et al. (2024) closes the visualization loop with a three-
pane visual analytics system: Outline View for agent trajectories, Agent View for event stacks with causal
29

Under review as submission to TMLR
arcs, and Monitor View for synchronized environment replay. This system transforms raw execution logs
into hierarchically structured behavioral narratives. A user study with 14 participants shows significant im-
provements overreplay-only baselineson complexanalyticaltasks. More specializedvisualizationtoolssuch
as claude-code-reverse reverse-engineer the interaction chains of specific coding agents, serving as research
artifacts for understanding harness-level behaviors Yu (2026).
7.3 Cost Tracking and Optimization
LLM inference is priced per token, and agent harnesses amplify cost exposure because a single user-facing
task may trigger dozens of LLM calls, each with its own prompt assembly, tool-result injection, and re-
sponsegeneration. Theobservabilityrequirementistwofold: tracking (knowingwheretokensarespent)and
optimization (spending fewer tokens for the same outcome).
Onthetrackingside,TensorZeroprovidesaunifiedLLMOpsstackthatbundlesgateway,observability,exper-
imentation,andoptimizationintoasingleservice,enablingper-callandper-taskcostattributionTensorZero
(2026). Heliconetakesaminimalistapproachasadrop-inproxythataddscostandlatencymonitoringwith
no code changes, making it particularly accessible for teams that want cost visibility without committing to
a full observability platform Helicone (2026).
Ontheoptimizationside,FrugalGPTChenetal.(2023)providesthefoundationalformulationbyproposing
threecost-reductionstrategies: promptadaptation, LLMapproximation, andLLMcascading. Itshowsthat
anadaptivecascadecanmatchGPT-4’sperformancewithupto98%costreductionbyroutingeasierqueries
to cheaper models. GPTCache Bang (2023) complements this approach with a semantic caching layer that
interceptsrepeatedorparaphrasedqueriesbeforetheyreachtheLLM,usingembeddingsimilaritytoretrieve
cached responses. Together, routing and caching have become recurring building blocks in production cost-
optimization stacks and are directly applicable to harness-level instrumentation, where each tool call and
context-assembly step can be independently metered and routed.
QC-Opt Shekhar et al. (2024) extends the routing paradigm with a quality-aware framework that jointly
optimizes model selection, token count, and latency under budget constraints, using a BertScore predictor
to estimate output quality without invoking the target model. The token elasticity phenomenon discovered
by TALE Han et al. (2025) reveals an important nuance: setting the token budget too low for chain-of-
thought reasoning can paradoxically increase token consumption, because the model overflows its budget
andgeneratesmoretokensthanamoderatelybudgetedpromptwould. Attheinfrastructurelevel,Dual-Pool
Token-Budget Routing Liu et al. (2026b) addresses cost from the serving side, partitioning a homogeneous
vLLMfleetintoshort-contextandlong-contextpoolsandroutingrequestsbasedonestimatedtokenbudget.
Evaluated on Azure LLM Inference traces and LMSYS-Chat-1M, the approach reduces GPU-hours by 31–
42% (projecting to $2.86M annual savings at A100 fleet scale).
For harness engineers, the implication is that cost observability must span multiple layers: API-level
token tracking (Helicone, TensorZero), application-level routing decisions (FrugalGPT, QC-Opt), and
infrastructure-level resource utilization (Dual-Pool, KV-cache occupancy). Anthropic’s study on infrastruc-
turenoiseinagenticcodingevaluationsAnthropic(2026a)providesacautionarycomplement: infrastructure
configurationalonecanshiftbenchmarkscoresby6percentagepoints(p<0.01). Thisfindingsuggeststhat
cost optimization and evaluation fidelity are tightly intertwined, since cutting resources to save cost can
silently degrade agent performance in ways that remain invisible without fine-grained observability.
7.4 Reliability Engineering
Failure recovery, checkpoint/resume, retry strategies, and session recovery are harness-level concerns that
determine whether a long-running agent can survive transient failures. These concerns become acute when
agents operate across multiple context windows, where each new session begins with no memory of what
camebeforeAnthropic(2025d). Anthropic’sharnessengineeringworkidentifiesfourrecurringfailuremodes
inlong-runningcodingagents: theagentattemptstoone-shottheentiretask, theagentdeclarestheproject
complete prematurely, the agent leaves the environment in a broken state between sessions, and the agent
marks features as done without proper testing. Their two-part solution directly addresses these reliability
30

Under review as submission to TMLR
concerns through harness design rather than model improvement Anthropic (2025d). It uses an initializer
agent to decompose the task into a structured feature list and set up progress-tracking artifacts, including
a git repo, progress file, and init script, followed by a coding agent that works incrementally on one feature
at a time while leaving clean handoff state.
Subsequent work extends this pattern. Anthropic’s GAN-inspired three-agent architecture (planner, gener-
ator, evaluator) introduces sprint contracts and separated self-evaluation to address the tendency of agents
toover-praisetheirownworkAnthropic(2026c). Notably, theauthorsdemonstratethatharnesscomplexity
should track model capability: when upgrading from Opus 4.5 to Opus 4.6, they removed the sprint con-
struct and context resets entirely, reducing cost from $200 to $125 while maintaining output quality. This
illustratesageneralprinciple: every harness component encodes an assumption about what the model cannot
do on its own, and those assumptions go stale as models improve.
At the infrastructure level, Anthropic’s Managed Agents architecture Anthropic (2026b) decouples the
“brain” (harness + LLM) from the “hands” (sandboxes and tools) and the “session” (durable event log),
making each independently recoverable. If the harness crashes, a new instance can be rebooted with
wake(sessionId) and resume from the last event in the session log. If a sandbox fails, the harness catches
the error as a tool-call failure and provisions a new one. Credentials are stored in an external vault, never
entering the sandbox. This architecture transforms all components from “pets” (irreplaceable, hand-tended
instances) into “cattle” (interchangeable, automatically reprovisioned), a prerequisite for operating agents
reliably at scale.
The academic literature provides taxonomies of the failure modes that reliability engineering must address.
MASTCemrietal.(2025)identifies14failuremodesacrossmulti-agentsystems,clusteredintosystemdesign
issues,inter-agentmisalignment,andtaskverificationproblems(κ=0.88). AgentErrorTaxonomyZhuetal.
(2025) decomposes failures by module (memory, reflection, planning, action, system) and shows that error
propagation—a single root-cause failure cascading through subsequent decisions—is the central reliability
bottleneck. TheirAgentDebugframeworkyieldsupto26%relativeimprovementintasksuccessbyisolating
root causes rather than treating surface symptoms. Meanwhile, Vinay (2025) contributes a system-level
taxonomyof15hiddenfailuremodesspecifictoproductionLLMdeployments,includingversiondrift (model
updates silently changing behavior), cost-driven performance collapse (aggressive optimization degrading
quality), and multi-step reasoning drift (gradual coherence loss over long sequences). QSAF Atta et al.
(2025)formalizescognitive degradation asasix-stagelifecyclevalidatedacrossfiveLLMplatforms,revealing
that hallucinated outputs can be stored in persistent memory and reused in future sessions, creating self-
reinforcing degradation loops that cross session boundaries.
Forruntimedetection,SentinelAgentHeetal.(2025)modelsmulti-agentinteractionsasagraphandclassifies
anomaliesatthreetiers(global,single-point,multi-point)usingLLM-as-judgewithhuman-in-the-looppolicy
refinement. AgentFixerMulianetal.(2026)deploys15validationtoolsonIBM’sCUGAproductionsystem,
achieving 64–88% issue detection rates and finding that 38% of task failures trace to parsing errors—a
failuremodefullyaddressablebydeterministicchecks. Thepracticalimplicationisthatreliabilityforagents
requires a layered detection strategy: lightweight rule-based checks for structural failures (malformed tool
calls, schema violations), statistical monitoring for performance drift (latency, token usage, cost trends),
andLLM-basedsemanticanalysisforreasoningfailures(hallucination,plan-actionmisalignment,premature
stopping).
7.5 Discussion: Toward Unified Observability
The observability–evaluation gap. The LangChain survey’s 89%/52% split reflects a structural discon-
nect: trace-collectiontoolsandevaluationframeworkshavelargelybeendevelopedbydifferentcommunities
with different interfaces. Closing this gap requires tighter integration, such as automatically generating
regression test cases from production failure traces, or using online evaluation scores as alerting signals.
LangChain’s own analysis of deep-agent evaluation LangChain (2025a) and Anthropic’s quantification of
infrastructure noise Anthropic (2026a) both argue that evaluation and observability must be treated as a
single feedback loop rather than separate concerns.
31

| Under review | as     | submission |     | to TMLR |                 |     |          |            |        |          |          |
| ------------ | ------ | ---------- | --- | ------- | --------------- | --- | -------- | ---------- | ------ | -------- | -------- |
|              |        |            |     | Tools   | like TensorZero | and | Langfuse | are moving | toward | bundling | gateway, |
| Unified      | LLMOps | stacks.    |     |         |                 |     |          |            |        |          |          |
observability, evaluation, and optimization into a single platform, reducing integration overhead. The
NLAH framework pushes this further by making the harness itself modular and introspectable, with each
component’s contribution quantifiable through ablation. Anthropic’s Managed Agents architecture takes
the infrastructure-level view, virtualizing harness components into substitutable interfaces (execute(),
emitEvent(),getEvents())thatcanaccommodatefutureharnessdesignswithoutchangingthesurrounding
system.
|                           |     |     |     |            | Every | harness | component | encodes | an assumption |     | about what |
| ------------------------- | --- | --- | --- | ---------- | ----- | ------- | --------- | ------- | ------------- | --- | ---------- |
| The harness-as-assumption |     |     |     | principle. |       |         |           |         |               |     |            |
the model cannot do on its own Anthropic (2026c). As models improve, observability systems must detect
not only when agents fail, but also when harness components have become unnecessary overhead. The ideal
observability system would include a meta-monitoring layer that tracks which interventions (context resets,
evaluator feedback loops, tool restrictions) are still load-bearing, enabling continuous harness simplification
| alongside      | model | upgrades. |            |     |     |     |     |     |     |     |     |
| -------------- | ----- | --------- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 Verification |       | and       | Evaluation |     | (V) |     |     |     |     |     |     |
Verification and Evaluation (V) is the sixth pillar of ETCLOVG (Claim 2 in §1). The systems and bench-
marks we discuss are drawn from the 170+ project corpus that supports Claim 3.
SWE-bench(Jimenezetal.,2024),Terminal-Bench(Merrilletal.,2026),WebArena(Zhouetal.,2024),
TaskandBenchmark VisualWebArena(Kohetal.,2024),BrowserGym(Chezellesetal.,2024),WorkArena(Drouinetal.,2024),
|     |     | Grounding |     |     | OSWorld(Xieetal.,2024),AgentBench(Liuetal.,2023a),GAIA(Mialonetal.,2023), |     |     |     |     |     |     |
| --- | --- | --------- | --- | --- | ------------------------------------------------------------------------- | --- | --- | --- | --- | --- | --- |
TheAgentCompany(Xuetal.,2024),WorkArena++(Boisvertetal.,2024)
|     |     |          |                |        | R ep o 2 | R u n ( H u e t a l . ,    | 2 0 2 5 a ) , H A | L ( K a p o o r e t a l., 20 2 | 5 ), S W E - a g e n t ( Yangetal.,2024), |     |     |
| --- | --- | -------- | -------------- | ------ | -------- | -------------------------- | ----------------- | ------------------------------ | ----------------------------------------- | --- | --- |
|     |     | P r e-   | E xe c u t i o | n      | S W E -  | R e X ( S W E - a g e nt   | T e a m , 2 0 2   | 4 ) , O p e n H a n d s (W a   | n g e t al. , 2 0 2 5 b ) ,               |     |     |
|     |     | Rea d in | e ss V a l i d | a tion | L L M -  | a s - J ud g e S u r v e y | ( G u e t a l. ,  | 2 0 2 4 )                      |                                           |     |     |
&noitacfiireV
noitaulavE
|     |     |             |               |          | S W E -  | a g e n t (Y a n g e t a    | l. , 2 0 2 4 ) , O  | p e n H a n d s ( W a n g e t    | a l . ,2025b),SWE-ReX(SWE-agentTeam,2024), |     |     |
| --- | --- | ----------- | ------------- | -------- | -------- | --------------------------- | ------------------- | -------------------------------- | ------------------------------------------ | --- | --- |
|     |     | C o n tr ol | l e d E x e c | u t io n | H A L    | ( K a p o o r e t a l . , 2 | 0 2 5 ) , R 2 E - G | y m ( J a in e t a l ., 2 0 2    | 5 ) ,                                      |     |     |
|     |     | a n d T     | r a c e C a p | t u r e  | L a n gC | h a i n D ee p - A g e n    | t E v a l u a ti o  | n ( L a n g C ha i n , 2 0 2 5 b | )                                          |     |     |
ReAct(Yaoetal.,2023),G-Eval(Liuetal.,2023b),
Multi-LevelJudgement MT-BenchandChatbotArena(Zhengetal.,2023),LLM-as-JudgeSurvey(Guetal.,2024),
|     |     | andFailureAttribution |     |     | SWE-bench(Jimenezetal.,2024),OSWorld(Xieetal.,2024), |     |     |     |     |     |     |
| --- | --- | --------------------- | --- | --- | ---------------------------------------------------- | --- | --- | --- | --- | --- | --- |
Terminal-Bench(Merrilletal.,2026),HAL(Kapooretal.,2025)
AnthropicEvals(Anthropic,2026b),
|     |     | C o nt i n u | o u s R e g r | e s si o n | L a n g C | h a i n D e e p - A g e n | t E v a l u a t i o | n ( L a n g C h a in , 20 2 5 b | ) , |     |     |
| --- | --- | ------------ | ------------- | ---------- | --------- | ------------------------- | ------------------- | ------------------------------- | --- | --- | --- |
an d D e p l o y m e n t F e e d b a ck p r o m p t f o o ( p r o m p t f o o c o n t r i b u t o r s , 2 0 2 6 ) , D e e p E v a l (C o nfi d e n t A I , 2 0 2 6) , R AG A S ( E s e t a l. , 2024),
|     |     |     |     |     | lm - e v | a l u a t io n - h a r n e s s | ( G a o e t a l ., | 2 0 2 1 ), R e p r o d u c i b l e | L M E v a l u at i o n ( B id | e rm an e t a l. , 2 02 | 4 ) , |
| --- | --- | --- | --- | --- | -------- | ------------------------------ | ------------------ | ---------------------------------- | ----------------------------- | ----------------------- | ----- |
verifiers(PrimeIntellect,2026),R2E-Gym(Jainetal.,2025),Meta-Harness(Leeetal.,2026)
Figure 11: Representative work on verification and evaluation for LLM agents, organized by the chapter’s
| task-to-feedback |            | lifecycle. |     |                    |     |           |     |     |     |     |     |
| ---------------- | ---------- | ---------- | --- | ------------------ | --- | --------- | --- | --- | --- | --- | --- |
| 8.1 Harness      | Evaluation |            | as  | a Task-to-Feedback |     | Lifecycle |     |     |     |     |     |
A harness-aware evaluation should treat the reported score as a property of the model–harness pair, not
of the model alone. This motivates evaluation protocols that either lock the harness across models or vary
harness configurations as an explicit experimental factor (Bölük, 2026b). We organize harness evaluation as
a task-to-feedback lifecycle: a structured process that begins with defining what an agent is asked to do and
ends with feeding evaluation results back into harness improvement. Figure 12 summarizes this five-stage
task-to-feedbacklifecycle. ThislifecyclebuildsonakeydifferencebetweenconventionalLLMevaluationand
agent evaluation. Conventional LLM evaluation primarily scores outputs on fixed inputs, whereas harness
evaluation measures an execution episode: a task is grounded in an environment, the agent interacts with
tools and state over time, traces are captured, and the evaluator judges both the final result and the path
taken to reach it (Kapoor et al., 2025; Anthropic, 2026b; LangChain, 2025b).
Acentralmotivationforthislifecycleisthatevaluationinfrastructurenoisecanmasqueradeasmodelfailure:
failed runs may reflect not only model limitations, but also broken tools, stale context, non-reset sandboxes,
flaky tests, benchmark ambiguity, or unstable judges (Kapoor et al., 2025; Hu et al., 2025a; Jimenez et al.,
2024). Thus, evaluation should convert agent behavior into structured judgements, failure attribution, and
| regression | feedback, | rather | than | merely | reporting | a final | score. |     |     |     |     |
| ---------- | --------- | ------ | ---- | ------ | --------- | ------- | ------ | --- | --- | --- | --- |
32

| Under | review | as  | submission | to  | TMLR |     |     |     |     |
| ----- | ------ | --- | ---------- | --- | ---- | --- | --- | --- | --- |
Figure12: Thetask-to-feedbacklifecycleforharnessevaluation. SectionVorganizesverificationandevalu-
ationasafive-stagequality-controlloop: taskandbenchmarkgrounding,pre-executionreadinessvalidation,
controlledexecutionandtracecapture,multi-leveljudgementandfailureattribution,andcontinuousregres-
sion and deployment feedback. The figure emphasizes that harness evaluation should not only report final
success rates, but also diagnose failure sources and feed the resulting evidence back into systematic harness
improvement.
The five-stage decomposition follows the causal path of an agent evaluation run. Before an agent can
be evaluated, the benchmark must specify the task, environment, tools, constraints, and success criteria.
Before execution, the setup must be validated so that environment or grader failures are not mistaken for
model failures. During execution, the harness must capture traces that make the run diagnosable. After
execution,thesystemmustjudgetheoutcome,trajectory,andevaluatorreliability,thenattributefailuresto
likely harness components. Finally, the resulting diagnosis should feed back into regression tests and future
harness revisions. In this view, evaluation is not a terminal scoring step, but a quality-control loop over the
| full | agent    | harness. |            |        |              |     |     |     |     |
| ---- | -------- | -------- | ---------- | ------ | ------------ | --- | --- | --- | --- |
| We   | organize | the      | discussion | around | five stages. |     |     |     |     |
• Task and Benchmark Grounding defines what is being evaluated, in which environment, with
|     | which         | tools, | constraints, |           | and success | criteria (§8.2). |              |               |                |
| --- | ------------- | ------ | ------------ | --------- | ----------- | ---------------- | ------------ | ------------- | -------------- |
|     | •             |        |              |           |             | checks whether   | the sandbox, | dependencies, | tools, context |
|     | Pre-execution |        |              | Readiness | Validation  |                  |              |               |                |
state,permissionpolicies,budgets,andgradersarecorrectlyinitializedbeforetheagentruns(§8.3).
• Controlled Execution and Trace Capture runs the agent under reproducible conditions while
recording model outputs, tool calls, state changes, errors, retries, cost, and latency (§8.4).
|     | •           |     |           |     |             |             | evaluates | the run at the outcome, | trajectory, |
| --- | ----------- | --- | --------- | --- | ----------- | ----------- | --------- | ----------------------- | ----------- |
|     | Multi-level |     | Judgement |     | and Failure | Attribution |           |                         |             |
and evaluator levels, then localizes likely failure sources across the harness stack (§8.5).
• Continuous Regression and Deployment Feedback converts evaluation outcomes into regres-
sion tests, monitoring signals, and engineering feedback for subsequent harness revisions (§8.6).
| 8.2 | Stage | 1: Task | and | Benchmark | Grounding |     |     |     |     |
| --- | ----- | ------- | --- | --------- | --------- | --- | --- | --- | --- |
Thefirststageaskswhatisbeingevaluated. ForLLMagents,ataskisnotsimplyanatural-languageprompt,
but an embedded problem defined by an environment state, available tools, allowed actions, constraints,
33

Under review as submission to TMLR
terminationconditions,andsuccesscriteria. Taskgroundingisthereforethefoundationofharnessevaluation:
without a well-specified environment and success condition, later scores cannot be interpreted reliably.
8.2.1 Software Engineering and Terminal Tasks
Softwareengineeringbenchmarksareamongthemostmatureformsofagentevaluationbecausetheycombine
realistic tasks with executable outcome verification. SWE-bench grounds each task in a real GitHub issue
and repository snapshot, then evaluates whether the generated patch resolves the issue by running tests
(Jimenez et al., 2024). Terminal-Bench extends this idea to command-line workflows, where agents interact
with terminal environments by editing files, running commands, setting up dependencies, and interpreting
failures (Merrill et al., 2026). The key insight from this category is that strong outcome verifiers require
strong task grounding. Tests can only serve as reliable evaluators when the repository state, dependencies,
and intended success criteria are precisely specified. Otherwise, a failed test may reflect an invalid patch,
but it may also reflect an inconsistent environment or an underspecified benchmark instance.
8.2.2 Web, Browser, and Computer-Use Tasks
Web and computer-use benchmarks ground tasks in interactive environments where success is defined by
browser, desktop, or application state changes. WebArena introduced realistic web environments for au-
tonomous agents (Zhou et al., 2024); VisualWebArena adds multimodal web tasks (Koh et al., 2024);
BrowserGym provides a common browser-agent research substrate (Chezelles et al., 2024); and WorkArena
focusesonServiceNow-basedknowledgework(Drouinetal.,2024). OSWorldfurtherbroadensevaluationto
realcomputerenvironmentsinvolvingdesktopapplications,files,andmulti-applicationworkflows(Xieetal.,
2024). These benchmarks show that browser and computer-use evaluation is simultaneously an evaluation
problem and an environment-design problem. The benchmark must provide a realistic interface, isolate
task state, expose appropriate observations, and define measurable success predicates. This creates a direct
bridge between the execution environment layer and the evaluation layer.
8.2.3 Cross-Domain and Enterprise Workflow Tasks
A third group of benchmarks tests broader agent capabilities across heterogeneous tools, environments,
and workflows. AgentBench evaluates LLM agents across operating systems, databases, web browsing, and
games(Liuetal.,2023a);GAIAtargetsgeneralassistanttasksrequiringreasoning,tooluse,andmultimodal
informationaccess(Mialonetal.,2023); andTheAgentCompanysimulatesworkplace-styledigitallabor(Xu
etal.,2024). WorkArenaandWorkArena++furtheremphasizeenterpriseworkflows,wheresuccessdepends
onnavigatingcomplexsoftwareratherthanansweringisolatedquestions(Drouinetal.,2024;Boisvertetal.,
2024). Themaincontributionofthisbenchmarkfamilyiscoverage: ittestswhetheraharnesscangeneralize
across task types, tool interfaces, state representations, workflows, and success conditions.
8.3 Stage 2: Pre-execution Readiness Validation
Thesecondstageaskswhethertheevaluationcanberunfairlyandreproducibly. Thisstageisofteninvisible
inbenchmarkleaderboards,butitiscentraltoharnessevaluation. Beforeanagentbegins,theharnessmust
validatethattheenvironment,tools,contextstate,permissionboundaries,budgetconstraints,andevaluators
are correctly initialized. Without this readiness layer, downstream failures become difficult to attribute: a
failed run may be caused by the agent, but it may also be caused by the evaluation setup.
8.3.1 Environment and Sandbox Readiness
Environment readiness checks whether the sandbox, repository, browser, terminal, or VM starts from a
known baseline. In software engineering, this includes the repository snapshot, dependencies, task setup,
and test executability; in browser and computer-use settings, it includes website resets, browser profiles,
desktop state, and service availability.
Severalsystemsmakethisproblemexplicit. SWE-benchreliesonexecutablerepositorystatesandtest-based
verification(Jimenezetal.,2024);Terminal-Benchpackagesterminaltaskswithcontrolledenvironmentsand
34

Under review as submission to TMLR
verification logic (Merrill et al., 2026); and OSWorld uses real computer environments with execution-based
evaluation scripts (Xie et al., 2024). Repo2Run targets dependency and environment setup by automating
executable Docker environments for repositories (Hu et al., 2025a), while HAL emphasizes standardized,
cost-aware evaluation infrastructure for agents (Kapoor et al., 2025). Together, these systems show that
environment reset and dependency validation are part of the measurement instrument.
8.3.2 Tool, Context, and Permission Readiness
Readiness validation is cross-layer. Tool readiness checks whether APIs, MCP servers, browser controls,
shell commands, and file operations are available and consistently described. Context readiness checks
whetherhistories,memorystores,scratchpads,andretrieveddocumentsareresetorintentionallyinitialized.
Permission readiness checks whether file access, credentials, network access, and approval gates match the
benchmark specification.
Thisstageconnectsevaluationtothetool,context,andgovernancelayers. Iftooldescriptionschangeacross
runs, thebenchmarknolongermeasuresthesameactionspace. Ifmemoryorcontextisnotreset, theagent
may benefit from leaked state. If permissions are too restrictive, a capable agent may fail for governance
reasons; if they are too permissive, unsafe or benchmark-exploiting behavior may go undetected. Systems
such as SWE-agent, SWE-ReX, and OpenHands illustrate that tool exposure, shell access, browser access,
execution backends, and runtime interfaces are not separable from evaluation design: the agent-computer
interface determines what actions are possible and therefore what a benchmark actually measures (Yang
et al., 2024; SWE-agent Team, 2024; Wang et al., 2025b). A rigorous evaluation harness should therefore
record these configurations, including the tool registry, context policy, permission policy, budget, timeout,
model configuration, and runtime interface, as evaluation metadata.
8.3.3 Evaluator and Grader Readiness
The evaluator itself must also be validated before execution. Deterministic graders should be checked for
flakiness, missing dependencies, and compatibility with environment state; LLM-as-Judge prompts, rubrics,
and judge models should be versioned; and human-audit protocols should be defined in advance.
InbenchmarkssuchasSWE-bench,executabletestsprovidescalableoutcomeverification,butscorevalidity
still depends on correct environment setup, task specification, and test reliability (Jimenez et al., 2024). For
open-ended tasks, LLM-as-Judge systems require calibration, bias mitigation, and consistency checks rather
than blind reuse of a strong model as a grader (Zheng et al., 2023; Gu et al., 2024). Evaluator readiness is
therefore a prerequisite for meaningful failure attribution.
8.4 Stage 3: Controlled Execution and Trace Capture
The third stage asks what happened during execution. In conventional LLM evaluation, the evidence may
consist of a single input-output pair. In agent evaluation, the trace is a multi-step trajectory: the model
observes state, reasons, calls tools, receives tool outputs, modifies the environment, handles errors, and
eventuallyterminates. Controlledexecutionandtracecapturearethereforenecessaryforturningbenchmark
runs into diagnosable evidence.
8.4.1 Controlled Rollouts and Reproducible Execution
Arolloutisthebasicunitofagentevaluation. Itincludesthetask,modelconfiguration,harnessconfiguration,
action sequence, intermediate observations, final state, and grading result. A controlled rollout fixes key
sources of accidental variation, including environment state, tool availability, timeout, budget, permission
policy, and evaluator version. When nondeterminism remains, repeated rollouts can expose variance rather
than hiding it behind a single score.
Several systems illustrate this need for reproducible execution. SWE-agent exposes agents to repository
navigation, file editing, and test execution as part of the interaction loop (Yang et al., 2024). OpenHands
combines code editing, command-line execution, browser interaction, sandboxed execution, and benchmark
integration (Wang et al., 2025b). SWE-ReX abstracts over local and remote sandboxed shell environments
35

Under review as submission to TMLR
so that execution backends can change without changing agent logic (SWE-agent Team, 2024). LangChain
further decomposes deep-agent evaluation into single-step validation, full-turn evaluation, and multi-turn
simulation (LangChain, 2025b). Together, these systems show that reproducibility requires replaying the
full model–tool–environment interaction, not merely rerunning a model call.
8.4.2 Trace-Native Evaluation
Trace capture converts binary scoring into causal diagnosis. A trace-native harness should record model
outputs, tool calls, tool results, environment state changes, context snapshots, errors, retries, recovery ac-
tions, token usage, latency, and cost. These traces distinguish superficially similar failures: one agent may
never find the relevant file, while another may find it but produce an invalid patch. They can also reveal
undesirable success, such as benchmark exploitation, excessive tool calls, or permission violations.
HAL treats logs and traces as first-class artifacts for standardized agent evaluation, using large-scale agent
logstoinspectbehaviorsthatfinalscoresmayhide(Kapooretal.,2025). R2E-Gymsimilarlylinksexecutable
trajectories and hybrid verifiers to both test-time evaluation and training-time feedback (Jain et al., 2025).
For harness engineering, traces are therefore not auxiliary debugging artifacts; they are primary evaluation
data.
8.4.3 Cost, Latency, and Resource Tracking
Agent evaluation should report not only quality, but also the cost of achieving it. Long-horizon agents may
improve success rates by spending more tokens, calling more tools, retrying more often, or using stronger
models. A harness-level evaluation should therefore track token usage, model cost, wall-clock latency, tool-
call count, retry count, and resource consumption.
Rather than ranking agents only by success rate, evaluations should expose a success-cost-latency fron-
tier. HAL explicitly frames agent evaluation as standardized and cost-aware (Kapoor et al., 2025), while
LangChain’s deep-agent evaluation guidance emphasizes reproducible environments and multi-granularity
evaluation for comparing cost-quality trade-offs (LangChain, 2025b). This is especially important for de-
ployed agent services, where the unit of optimization is a recurring workload under budget and latency
constraints.
8.5 Stage 4: Multi-level Judgement and Failure Attribution
After controlled execution and trace capture, the central question is how the run should be judged and, if it
fails, how the failure should be localized. We define Stage 4 as a combined process of multi-level judgement
andfailure attribution. Multi-leveljudgementevaluatestherunatthreelevels: whetherthefinaloutcomeis
correct, whether the trajectory is efficient and policy-compliant, and whether the evaluator itself is reliable.
Failure attribution then uses these signals to diagnose where the failure most likely originated, such as the
model, toolinterface, contextmanager, executionenvironment, orchestrationloop, benchmarkspecification,
or evaluator. This stage is what distinguishes harness evaluation from ordinary benchmark evaluation: the
goal is not merely to assign a score, but to convert execution evidence into actionable engineering diagnosis.
8.5.1 Outcome-level Evaluation
Outcome-level evaluation measures whether the final task objective was achieved. In software engineering,
this is often operationalized through unit tests, regression tests, or issue-specific verification, as in SWE-
bench (Jimenez et al., 2024). In terminal tasks, outcome evaluation may depend on final files, command
outputs, or task-specific checkers (Merrill et al., 2026). In browser and enterprise workflow benchmarks, it
often depends on final environment state, such as whether a form was submitted, a ticket was updated, or
a configuration was changed (Zhou et al., 2024; Drouin et al., 2024). In general assistant benchmarks such
as GAIA, the outcome may be an answer string or structured response (Mialon et al., 2023).
The strength of outcome-level evaluation is scalability and interpretability: it provides a clear task-level
success signal and supports leaderboard comparison. Its limitation is compression. A full execution episode
isreducedtoonevalue,hidingwhethertheagentsucceededrobustly,safely,orefficiently. Outcomeevaluation
36

Under review as submission to TMLR
is therefore necessary but not sufficient. It answers whether the task was completed, but not whether the
harness produced a trustworthy execution.
8.5.2 Trajectory-level Evaluation
Trajectory-levelevaluationmeasuresthequalityofthepathtakenbytheagent. Itaskswhethertheagentse-
lectedappropriatetools, orderedactionssensibly, avoidedredundantcalls, respectedpermissionboundaries,
recovered from errors, and maintained context consistency over time. This level is where agent evaluation
diverges most clearly from conventional output evaluation: a final answer can be correct while the trajec-
tory is still unacceptable, for example if the agent wastes excessive tokens, repeatedly calls irrelevant tools,
violates permissions, or relies on brittle benchmark-specific behavior.
ReAct provides a conceptual foundation for trajectory-level analysis by representing agent behavior as in-
terleaved reasoning, acting, and observing steps (Yao et al., 2023). Modern agent benchmarks extend this
view into richer environments where each action changes the state available to future steps. WebArena,
WorkArena, OSWorld, and Terminal-Bench all produce trajectories whose intermediate actions are mean-
ingful evaluation objects rather than hidden implementation details (Zhou et al., 2024; Drouin et al., 2024;
Xie et al., 2024; Merrill et al., 2026). LangChain’s evaluation patterns likewise emphasize single-step and
full-turn evaluations because they allow developers to inspect decision quality before an entire run succeeds
or fails (LangChain, 2025b).
Trajectory-level judgement is especially valuable for harness engineering because it provides a route from
failuretorepair. Ifanagentfailsbecauseitchoosesthewrongtool,thetoolinterfacemayneedimprovement.
If it forgets prior constraints, the context layer may need adjustment. If it loops without recovery, the
orchestration layer may need lifecycle controls. Thus, trajectory evaluation turns benchmark results into
layer-specific engineering feedback.
8.5.3 Evaluator-level Evaluation
Evaluator-level evaluation asks whether the evaluator itself can be trusted. Deterministic verifiers, such as
unit tests or state-based checkers, are reproducible, cheap, and easy to compare across systems, but they
are narrow and difficult to design for open-ended tasks. LLM-as-Judge systems are flexible for natural-
language outputs and trajectory assessment, but they introduce bias, nondeterminism, and additional cost.
Human audits remain important for ambiguous or safety-critical cases, but they do not scale to continuous
evaluation.
G-Eval showed that LLM-based evaluators can better align with human judgements on NLG evaluation
tasks, while also highlighting bias toward LLM-generated text (Liu et al., 2023b). MT-Bench and Chatbot
Arena systematically studied LLM-as-Judge and identified position bias, verbosity bias, self-enhancement
bias, and limited reasoning ability (Zheng et al., 2023). Recent surveys further argue that reliable LLM-as-
Judge systems require standardization, bias mitigation, consistency checks, and meta-evaluation (Gu et al.,
2024).
Foragentharnesses,evaluator-levelevaluationisnotoptional. Ifagraderisflaky,atestisnondeterministic,
or an LLM judge is biased, then evaluation noise can be misattributed to the agent or model. A robust
harnessshouldthereforepreferlayeredgraders: deterministicchecksforobjectivestatechanges,LLMjudges
forsemanticortrajectory-levelassessment,andhumanauditsforambiguousorhigh-riskcases. Theevaluator
should be treated as a component under test, not as an oracle outside the system.
8.5.4 Failure Attribution Across Harness Layers
Failureattributionidentifieswhatshouldbefixedafterarunhasbeenjudged. Afailedrolloutmayoriginate
from model reasoning, tool-interface design, stale or compressed context, sandbox instability, orchestration
loops, benchmarkambiguity, orevaluatorunreliability(Kapooretal.,2025;Huetal.,2025a;Jimenezetal.,
2024; LangChain, 2025b). Outcome-level signals indicate whether the objective was achieved; trajectory-
levelsignalsrevealwhethertheactionsequencewascoherent,efficient, andpolicy-compliant; evaluator-level
37

| Under review | as  | submission | to TMLR |     |     |     |     |     |
| ------------ | --- | ---------- | ------- | --- | --- | --- | --- | --- |
signalsindicatewhetherthescoreitselfistrustworthy. Together,thesesignalssupportdiagnosisratherthan
| mere scoring | (Kapoor | et  | al., 2025; | LangChain, |     | 2025b). |     |     |
| ------------ | ------- | --- | ---------- | ---------- | --- | ------- | --- | --- |
In practice, attribution is rarely a single-label classification problem. A vague task specification may cause
the agent to choose the wrong tool; an overly compressed context may cause it to forget a constraint; a
sandbox dependency issue may trigger recovery behavior that increases cost; or a flaky judge may obscure
a valid solution. For this reason, failure attribution should be understood as a diagnostic process over the
full trace rather than as a post-hoc label attached to the final score. The output of Stage 4 is therefore not
only a judgement, but a structured diagnosis that Stage 5 can feed back into regression testing and harness
improvement.
| 8.6 Stage | 5:  | Continuous | Regression |     | and Deployment |     | Feedback |     |
| --------- | --- | ---------- | ---------- | --- | -------------- | --- | -------- | --- |
The final stage asks how evaluation results drive the next harness revision. Agent harnesses evolve contin-
uously: prompts, tool schemas, MCP servers, context policies, sandbox images, orchestration loops, gover-
nance rules, and judge prompts may all change over time. Continuous evaluation turns benchmark results
| and production   |     | failures   | into a regression |         | system  | for | the harness itself. |     |
| ---------------- | --- | ---------- | ----------------- | ------- | ------- | --- | ------------------- | --- |
| 8.6.1 Regression |     | Evaluation | for               | Harness | Changes |     |                     |     |
Regression evaluation should be triggered by harness changes as well as model changes. Changes to tool
descriptions, context-compaction policies, sandbox images, permission rules, or judge prompts can alter
agent behavior or evaluation scores. Because harness components interact, local improvements can create
global regressions.
The practical pattern is to maintain a layered evaluation suite: unit-like tests for tool schemas and de-
terministic validators, single-step tests for local decisions, full-rollout tests for end-to-end completion, and
multi-turn simulations for long-horizon coherence. LangChain’s deep-agent evaluation guidance reflects this
layered view (LangChain, 2025b), while Anthropic frames evals as automated tests with explicit grading
| logic that       | can run | during     | development |        | (Anthropic, | 2026b).     |     |     |
| ---------------- | ------- | ---------- | ----------- | ------ | ----------- | ----------- | --- | --- |
| 8.6.2 Evaluation |         | Frameworks | and         | LLMOps |             | Integration |     |     |
General evaluation frameworks provide reusable infrastructure for continuous testing. Promptfoo sup-
ports prompt and LLM-application regression testing; DeepEval provides unit-test-like abstractions; RA-
GAS focuses on retrieval-augmented generation evaluation; and lm-evaluation-harness supports standard-
izedlanguage-modelevaluation(promptfoocontributors,2026;ConfidentAI,2026;Esetal.,2024;Biderman
etal.,2024;Gaoetal.,2021). Althoughthesetoolswerenotalldesignedforlong-runningagents,theyprovide
| building | blocks | for regression-oriented |     | harness |     | evaluation. |     |     |
| -------- | ------ | ----------------------- | --- | ------- | --- | ----------- | --- | --- |
Evaluation should also connect with observability. Production traces can become regression tests, and
evaluation failures can become observability signals. This link closes the loop between monitoring what
| happened             | and constructing |     | controlled    | tests | that       | reproduce | and diagnose | it. |
| -------------------- | ---------------- | --- | ------------- | ----- | ---------- | --------- | ------------ | --- |
| 8.6.3 Verifier-Based |                  | and | Training-Time |       | Evaluation |           |              |     |
A newer direction uses evaluators not only as offline metrics, but also as training signals and optimization
targets. Verifier-based environments and RL-style agent gyms, including R2E-Gym and verifiers, use envi-
ronmentfeedbackasrewardorvalidationsignalsforimprovingagentpoliciesandscaffolds(Jainetal.,2025;
Prime Intellect, 2026). This shifts evaluation from a post-hoc measurement step to an active component of
| agent training, |     | test-time | adaptation, | and | scaffold | selection. |     |     |
| --------------- | --- | --------- | ----------- | --- | -------- | ---------- | --- | --- |
Meta-Harness extends this direction by treating harness design itself as an object of automated search (Lee
et al., 2026). Instead of evaluating only which model performs best under a fixed harness, this view asks
which harness structure, prompting strategy, tool interface, or control loop produces more reliable agent
behavior. In this framing, evaluation is not the end of the pipeline; it is the signal that allows the harness
to improve.
38

| Under review | as submission | to TMLR |     |     |     |     |     |
| ------------ | ------------- | ------- | --- | --- | --- | --- | --- |
8.7 Summary
Verification and evaluation is the layer that turns agent behavior into engineering evidence. We have orga-
nized this layer as a task-to-feedback lifecycle. Stage 1 grounds tasks in realistic environments and success
criteria. Stage 2 validates that the evaluation setup is ready, fair, and reproducible. Stage 3 runs controlled
rollouts and captures traces. Stage 4 judges each run at the outcome, trajectory, and evaluator levels. Stage
5 feeds the results into continuous regression testing and harness improvement.
This lifecycle reframes evaluation from a leaderboard mechanism into a quality-control loop for agent har-
nesses. Afinalsuccessrateremainsuseful, butitisnolongersufficient. Forlong-runningagents, thecentral
evaluationquestionisnotonlywhethertheagentsucceeded,butwhyitsucceededorfailed,whetherthepath
was acceptable, whether the evaluator was trustworthy, and which harness component should be improved
next.
| 9 Governance | and             | Security (G)       |                       |                                    |                                   |                                    |           |
| ------------ | --------------- | ------------------ | --------------------- | ---------------------------------- | --------------------------------- | ---------------------------------- | --------- |
|              |                 |                    | P r o g e n t ( S h   | i et a l . , 2 0 2 5 a ) , C o n t | e x tu a l A g e n t S e c u r i  | ty ( T s a i & B a g d a s a r i   | an,2025), |
|              | P e r m is s    | io nM o d e l s    | A u t h e n ti c a te | d D e l e g a t io n ( S o u th    | e t a l. , 2 0 2 5 ) , S A G A    | (S y r o s e t a l . , 2 0 2 5 ) , |           |
|              | and I d e nt it | y M an a g e m ent | Is o l a t e G P T    | ( W u e t a l . , 2 0 2 5 ) , P e  | r m i s s i o n M a n i f e s t s | ( M a rr o e t a l. , 2 0 2 5 )    |           |
PromptShield(Jacobetal.,2024),DataSentinel(Liuetal.,2025),
|     |     |     | S h i el d Ag en t | ( C h e n e t a l. , 2 0 2 5 b ) | , C o n t ro lV a l ve (J h a | e t a l . , 2 0 2 5 ) , |     |
| --- | --- | --- | ------------------ | -------------------------------- | ----------------------------- | ----------------------- | --- |
LifecycleHooks
|     |     |     | C a M e L (D e b | e ne d e tt i e t a l ., 2 0 2 5 | ) , A g e n tS p e c (W a n g | e t a l . , 2 0 2 6 ) , |     |
| --- | --- | --- | ---------------- | -------------------------------- | ----------------------------- | ----------------------- | --- |
AgentDoG(Liuetal.,2026a)
InstructionHierarchy(Wallaceetal.,2024),
| &ecnanrevoG | C o m | p o n e n t  | S e c A l i g n ( C | h e n e t a l . , 2 0 2 5 a ) , L l | a m a G u a r d (I n a n e t    | a l., 2 0 2 3 ) ,   |     |
| ----------- | ----- | ------------ | ------------------- | ----------------------------------- | ------------------------------- | ------------------- | --- |
|             | H a   | rd e n i n g | M C P S a fe t y    | A u d i t ( R a d o s e v i c h &   | H a l l o r a n , 2 0 2 5 ) ,   |                     |     |
| ytiruceS    |       |              | Ju m p i n g t h e  | L in e ( T r a i l o f B i t s ,    | 2 0 2 5 ) , E T D I ( B h a t t | et al . , 2 0 2 5), |     |
SAFEFLOW(Lietal.,2025)
Claude’sConstitution(Anthropic,2026a),AutoHarness(AIMingLab,2026),
|     | Declarative   |     | ProgentPolicies(Shietal.,2025a),                       |     |     |     |     |
| --- | ------------- | --- | ------------------------------------------------------ | --- | --- | --- | --- |
|     | Constitutions |     | Formal-LLM(Lietal.,2024),VeriSafeAgent(Leeetal.,2025), |     |     |     |     |
AgentSpec(Wangetal.,2026)
AutoHarness(AIMingLab,2026),SAGA(Syrosetal.,2025),
|     | Audit          |     | AgentMonitor(Naihinetal.,2023),AgentAuditor(Luoetal.,2025),      |     |     |     |     |
| --- | -------------- | --- | ---------------------------------------------------------------- | --- | --- | --- | --- |
|     | Infrastructure |     | SentinelAgent(Heetal.,2025),OWASPLLMTop10(OWASPFoundation,2025), |     |     |     |     |
AgenticGovernancePractices(Shavitetal.,2023)
|     | Ag e n t | S e c u r ity | A t t a c k a n d D | e f en s e L a n d s c a p e (      | K i m e t a l . , 2 0 2 6 ) , C    | l aw e d a n d D a n g e r o u s   | ( C he n e t a l ., 2026), |
| --- | -------- | ------------- | ------------------- | ----------------------------------- | ---------------------------------- | ---------------------------------- | -------------------------- |
|     | L a n    | d s c a p e   | A g e n t D o jo (  | D e b e n e d e t ti e t a l . , 2  | 0 2 4 ) , J a i l b r e a k in g L | L M s ( A n dr i u s h c h e n k   | o et a l., 2 0 2 4 ),      |
|     |          |               | A d a p t iv e A t  | t a c k s ( N a s r e t a l . , 2 0 | 2 5 ) , S lo p s q u a t t i n g ( | S pr a c k l e n e t a l . , 2 0 2 | 5 )                        |
Figure 13: Representative work on governance and security for LLM agents, organized by the chapter’s
security categories.
This layer addresses how agent behavior is constrained, made safe, and held accountable. LLM agents
now execute shell commands, send emails, commit code, and invoke third-party APIs; for production de-
ployments, a central question is under what constraints they should act and who bears accountability when
thoseconstraintsfail. Inproductionsystems,governancehasitsowntoolingecosystem,includingpermission
engines,policylanguages,auditpipelines,andgatewaycontrols. Thisecosystemisdistinctfromthelifecycle
hooks and observability infrastructure covered in Sections 6 and 7, warranting treatment as an independent
layer in the ETCLOVG taxonomy. We organize the discussion around five mechanisms: permission models
and identity management (§9.1), lifecycle hooks (§9.2), component hardening (§9.3), declarative constitu-
tions (§9.4), and audit infrastructure (§9.5). We then situate these mechanisms within the broader agent
| security landscape | (§9.6) | and close with | open research | directions | (§9.7). |     |     |
| ------------------ | ------ | -------------- | ------------- | ---------- | ------- | --- | --- |
| 9.1 Permission     | Models | and Identity   | Management    |            |         |     |     |
The first governance question for any agent harness is access control: which tools, files, network endpoints,
and system resources can the agent reach? Agent workloads make this harder than conventional RBAC or
ABAC because the required tool set often depends on a natural-language task that is unknown at deploy-
ment time. The literature therefore moves along a granularity axis: static boundaries fixed at deployment,
contextual policies evaluated per tool call, and cross-boundary permissions for interactions outside the local
harness.
39

Under review as submission to TMLR
Static permission boundaries. Production coding agents commonly predefine a permission scope and
require escalation for actions outside it. Codex (OpenAI, 2025) runs shell commands in a sandbox with
restricted filesystem and network access, while Gemini CLI (Mullen & Salva, 2025) combines workspace-
scopedfileaccesswithcommandallowanddenylists. Theseboundariesareeasytoinspect,buttheycannot
express task-specific intent.
Moving beyond fixed rules requires expressing constraints that depend on the runtime context of each tool
call.
Context-dependentprivilegecontrol. Progent(Shietal.,2025a)introducesadomain-specificlanguage
(DSL) whose predicates range over tool names, arguments, and environment state. The runtime evaluates
these predicates before each invocation, allowing least-privilege policies to vary by role, user, or session.
Conseca(Tsai&Bagdasarian,2025)pushesthisideafurtherbygeneratingatask-specificpolicyfromtrusted
context and enforcing it with a separate deterministic checker. The separation between policy generation
and enforcement is important: the generative component can adapt to the task, while the enforcer remains
auditable.
Theprecedingapproachesoperatewithinasingleagentboundary. Multi-agentsettingsintroduceadditional
challenges around both access control and agent identity.
Identity management and inter-agent access control. Before granting access, a system must estab-
lish who is requesting it. South et al. (2025) argue that agents need authenticated delegation: a framework
extending OAuth 2.0 and OpenID Connect with User ID Tokens, Agent ID Tokens, and scoped Delegation
Tokens that would bind user intent to agent-specific permissions. This token chain would create a verifi-
able accountability trail from human principal to agent action. SAGA (Syros et al., 2025) builds on this
principle for multi-agent settings through a provider-mediated architecture. Agents register with crypto-
graphic one-time keys, and short-lived access tokens enforce user-defined contact policies between agents.
IsolateGPT (Wu et al., 2025) takes an architectural approach, adopting a hub-and-spoke model where each
third-party application executes in an isolated spoke with its own LLM, memory, and tool access. Inter-
spoke communication passes through a trusted hub, so cross-application data exchange becomes an explicit
governance decision rather than an incidental side effect of a shared context window.
Credential management. Agents routinely handle API keys, session tokens, and one-time passwords.
Exposing these credentials to the LLM context creates exfiltration risk. Skyvern (Skyvern-AI, 2025) illus-
trates a common pattern: store secrets in a vault, expose only placeholders to the LLM, and substitute raw
valuesonlyattheautomationlayerthatexecutestheauthenticatedaction. Theunresolvedproblemissecret
lifecycle management for long-horizon sessions, where tokens may expire or be revoked mid-trajectory and
renewed credentials must still remain outside the model context.
Web-level permission coordination. The mechanisms above operate within a single harness’s trust
boundary and govern one deployment. Cross-organizational interactions, where agents traverse third-party
websites or call services owned by other parties, require coordination that no single harness can enforce
in isolation. Marro et al. (2025) propose agent-permissions.json, a lightweight manifest file analogous
to robots.txt. Website owners can declare which UI elements agents may use, rate limits, concurrency
constraints, and actions that require human confirmation. Such manifests do not solve authentication, but
they show how governance begins to cross organizational boundaries.
Open challenges. Designing permission models that are both expressive and usable is an unsolved prob-
lem. Overlyrestrictivepoliciesdegradeagentutility;overlypermissiveonesnegatethepurposeofgovernance.
The community has not converged on a standard permission specification language that is portable across
harness implementations. Open questions also persist about whether actions should be attributed to the
human operator, the agent instance, or transient task identities (South et al., 2025).
40

| Under review  |     | as submission |     | to TMLR |     |     |     |     |     |     |     |
| ------------- | --- | ------------- | --- | ------- | --- | --- | --- | --- | --- | --- | --- |
| 9.2 Lifecycle |     | Hooks         |     |         |     |     |     |     |     |     |     |
Permission models define what is allowed. Lifecycle hooks define when policy checks fire. Many harnesses
expose hook points at each stage of the agent loop: before planning, before tool invocation, after tool
execution,andbeforeresponsedelivery. Thesehooksallowgovernancelogictobeinjectedwithoutmodifying
the agent’s core reasoning. Figure 14 situates the four hook points along a single tool-use cycle.
|     |     |       | H1      |     |     | H2                |      |              | H3  |          |     |
| --- | --- | ----- | ------- | --- | --- | ----------------- | ---- | ------------ | --- | -------- | --- |
|     |     | Input |         |     | LLM |                   | Tool |              |     | Response |     |
|     |     |       | InputGR |     |     | ActionGR          |      | Post-execIFC |     |          |     |
|     |     |       |         |     | H4: | Human-in-the-Loop |      |              |     |          |     |
Figure 14: Four hook points along one tool-use cycle. Solid boxes are agent components; dashed boxes are
governance hooks. H1 validates input before it reaches the LLM, H2 validates the proposed action before
toolexecution,H3mediatesinformationflowfromtooloutputbackintocontext,andH4gatesconsequential
| actions on    | user | approval. |       |             |     |       |            |          |             |            |          |
| ------------- | ---- | --------- | ----- | ----------- | --- | ----- | ---------- | -------- | ----------- | ---------- | -------- |
|               |      |           |       |             |     | Input | guardrails | validate | data before | it reaches | the LLM. |
| Pre-execution |      | hooks:    | input | guardrails. |     |       |            |          |             |            |          |
PromptShield (Jacob et al., 2024) and DataSentinel (Liu et al., 2025) train dedicated classifiers to detect
prompt injection payloads in user inputs and retrieved content. Rule-based detectors are strict but brittle.
Model-baseddetectors generalizebetterbutareslowerandsusceptibletoadaptiveattacks (Andriushchenko
| et al., 2024; | Nasr | et  | al., 2025). |     |     |     |     |     |     |     |     |
| ------------- | ---- | --- | ----------- | --- | --- | --- | --- | --- | --- | --- | --- |
The next enforcement point occurs between the LLM’s proposed action and the harness’s tool execution.
Beforeexecutingatoolcall,output
| Pre-invocationhooks: |     |     | outputguardrailsandactionvalidation. |     |     |     |     |     |     |     |     |
| -------------------- | --- | --- | ------------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- |
guardrailsinspecttheLLM’sproposedaction. ShieldAgent(Chenetal.,2025b)formalizessafetyconstraints
as verifiable predicates and checks each action against them. In multi-agent systems, ControlValve (Jha
et al., 2025) constrains the control-flow graph between agents and prevents unauthorized agent transitions,
addressing control-flow hijacking attacks where one agent redirects execution to another.
After a tool executes, the returned data must also be inspected before re-entering the LLM context.
|     |     |     |     |     |     |     |     |     | CaMeL | (Debenedetti | et al., |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ----- | ------------ | ------- |
Post-execution hooks: information flow control and taint tracking.
2025) implements capability-based information flow control. Every data value carries metadata tags that
track its provenance, distinguishing trusted user input from untrusted web retrieval. A custom interpreter
enforcesthatuntrusteddatacannotinfluencecontrol-flowdecisions. CaMeLseparatesplanningovertrusted
context from processing over untrusted content, trading some flexibility for a stronger control/data-flow
| boundary | on AgentDojo |     | (Debenedetti |     | et al., | 2024). |     |     |     |     |     |
| -------- | ------------ | --- | ------------ | --- | ------- | ------ | --- | --- | --- | --- | --- |
A complementary enforcement mechanism places the human user in the loop.
|                   |     |     |        | Several | widely | used | coding agents, | including | Codex, | Gemini | CLI, Cursor, |
| ----------------- | --- | --- | ------ | ------- | ------ | ---- | -------------- | --------- | ------ | ------ | ------------ |
| Human-in-the-loop |     |     | hooks. |         |        |      |                |           |        |        |              |
and OpenHands (Wang et al., 2025a), gate destructive or out-of-scope actions on explicit user approval.
Threedesigndimensionsshapethesehooks: validationscope(whichactionsrequireapproval),alertrichness
(how much context the user sees), and recurrence policy (allow-once versus allow-always). Felt et al. (2012)
showed that only 17% of Android users paid attention to permission dialogs during app installation, and
only3%correctlyansweredcomprehensionquestionsaboutthepermissionstheyhadgranted;agentapproval
dialogs may face analogous habituation and comprehension risks. Frequent requests lead users to approve
| dangerous | actions | reflexively, |     | while | infrequent | requests | leave | coverage | gaps. |     |     |
| --------- | ------- | ------------ | --- | ----- | ---------- | -------- | ----- | -------- | ----- | --- | --- |
Some systems treat hooks as a programmable enforcement substrate rather than as isolated classifiers.
AgentSpec (Wang et al., 2026) defines rules with triggers, predicates, and enforcement actions at plan, tool-
call, and response stages. AgentDoG (Liu et al., 2026a) shifts from single-action classification to trajectory-
| level diagnosis, |     | organizing | risks | by  | source, | failure mode, | and | consequence. |     |     |     |
| ---------------- | --- | ---------- | ----- | --- | ------- | ------------- | --- | ------------ | --- | --- | --- |
41

Under review as submission to TMLR
Openchallenges. Acrosscurrentsystems,hookAPIsremainheterogeneous. Wearenotawareofawidely
adopted standard that defines a universal hook interface for third-party governance modules. Hooks also
introduce latency, and the interaction effects between stacked hooks remain largely unstudied. A plausible
failure mode is that an upstream sanitizer alters the signals that a downstream detector relies on, leaving
the combined pipeline weaker than either component considered in isolation.
9.3 Component Hardening
Lifecycle hooks enforce governance at the harness level. Component hardening strengthens individual agent
components, specifically the LLM and the tools it invokes, against their specific vulnerabilities. A harness
benefits from hardened components because fewer malicious inputs survive to trigger governance hooks in
the first place.
Model hardening. ArootcauseofpromptinjectionisthatLLMstreatallinputtextwithequalpriority,
making them unable to distinguish system instructions from untrusted data. Wallace et al. (2024) propose
aninstructionhierarchythattrainsmodelstoprioritizeprivilegedinstructions(systemprompts)overlower-
privileged ones (user messages, tool outputs). Models learn to align with lower-level instructions when they
areconsistentwithhigher-levelconstraints,andtoignoreorrefusethemwhentheyconflict. SecAlign(Chen
et al., 2025a) formulates the same defense goal as preference optimization over prompt-injected inputs,
desirable responses, and undesirable responses.
These model-level defenses complement harness-level hooks. A hardened model rejects more injections at
inference time, reducing the load on downstream guardrails. However, model hardening alone is insufficient:
it addresses wrong instruction following in Kim et al.’s taxonomy but does not prevent unconstrained data
flow or unauthorized actions, which require system-level enforcement (Kim et al., 2026; Wei et al., 2026).
Classifier-based runtime hardening. Acomplementarylineofworkhardensthemodelboundarywith-
outmodifyingtheagentLLMitself,bydeployingsmallauxiliaryclassifiersthatscreeninputsandoutputsat
runtime. Llama Guard (Inan et al., 2023) fine-tunes a separate model to classify both user prompts and as-
sistant responses against a configurable safety taxonomy, returning per-category labels that the harness can
route to allow, block, or escalate decisions. Such classifiers offer two practical properties that training-time
hardening lacks: the taxonomy can be edited without retraining the agent model, and the same detector
can be reused across heterogeneous LLM backends. The cost is the latency budget discussed in §9.2: each
additional classifier adds a forward pass per tool-use cycle.
Model and classifier defenses harden the LLM boundary; the tool boundary requires its own protocol-level
treatment.
Tool hardening and MCP security. The Model Context Protocol (MCP) (Anthropic, 2024c) has
emerged as a common interface between agents and tools, but its initial specification lacks native secu-
rity primitives. This gap has attracted both attacks and defenses, and an official specification response.
Radosevich & Halloran (2025) demonstrate that widely used commercial LLMs can be coerced into using
MCPtoolstoexecutemaliciouscode,establishremoteaccess,andstealcredentials. TheirMcpSafetyScanner
uses a three-agent architecture (hacker, auditor, supervisor) to systematically discover such vulnerabilities.
TrailofBits(TrailofBits,2025)showthatMCPserverscanattackclientsbeforeausereverinvokesatool,
through poisoned tool descriptions that influence the LLM’s behavior at registration time.
Onthedefenseside,ETDI(Bhattetal.,2025)extendsMCPwithcryptographicallysignedandversionedtool
definitions, ensuring that any modification to a tool’s code, schema, or permissions requires a new signed
version. This prevents rug-pull attacks where a previously approved tool is silently updated to perform
malicious actions.
Protocol-level hardening. Beyond individual components, SAFEFLOW (Li et al., 2025) introduces
protocol-level enforcement for multi-agent systems. It combines fine-grained information flow control with
transactional execution semantics, so a violating tool call or inter-agent message can be rolled back rather
than propagated through shared state.
42

| Under review | as  | submission | to TMLR |     |     |     |     |     |     |     |
| ------------ | --- | ---------- | ------- | --- | --- | --- | --- | --- | --- | --- |
Agent governance must also address the tools and packages that agents invoke.
| Supply | chain | risks. |     |     |     |     |     |     |     |     |
| ------ | ----- | ------ | --- | --- | --- | --- | --- | --- | --- | --- |
Spracklen et al. (2025) analyze 576,000 code samples across 16 LLMs and find that open-source models
hallucinate nonexistent package names at a rate of 21.7%. Attackers can register these hallucinated names
on public repositories and inject malicious code, a technique termed “slopsquatting.” ETDI’s cryptographic
signatures address part of this problem for MCP tools, but package managers and retrieval sources remain
| outside | most agent | governance | stacks. |     |     |     |     |     |     |     |
| ------- | ---------- | ---------- | ------- | --- | --- | --- | --- | --- | --- | --- |
Open challenges. Model hardening and tool hardening address complementary threat surfaces, but no
unifiedframeworkconnectsthem. Ahardenedmodelmaystillinvokeacompromisedtool, andasignedtool
definition does not prevent misuse by a jailbroken model. Composing these defenses into a coherent stack
with quantifiable residual risk remains an open problem. As MCP adoption grows, its security extensions
become natural targets for standardization, yet interoperability and certification remain largely unsettled.
| 9.4 Declarative |     | Constitutions |     |     |     |     |     |     |     |     |
| --------------- | --- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- |
Embedding governance logic directly in application code makes policies opaque, hard to audit, and difficult
to update. A growing number of harnesses externalize governance rules into declarative configuration files,
most commonly in YAML format. These files serve as a machine-readable constitution for the agent.
Training-time constitutions: Anthropic’s Constitutional AI. Anthropic (Anthropic, 2026a) pub-
lishes a constitution organized as a four-tier priority hierarchy: safety (preserving human oversight), ethics
(honesty,harmavoidance),compliance(Anthropic’sguidelines),andhelpfulness(userrequests). Theconsti-
tution distinguishes hard constraints, such as absolute prohibitions on chemical, biological, radiological, and
nuclear (CBRN) assistance, from soft-coded defaults that operators may adjust within defined bounds. In
agentic settings, this structure suggests a principal hierarchy in which Anthropic’s policies override operator
| configurations, |     | which in | turn override |     | end-user preferences. |     |     |     |     |     |
| --------------- | --- | -------- | ------------- | --- | --------------------- | --- | --- | --- | --- | --- |
Training-time constitutions operate by shaping the model’s behavior during alignment and post-training.
They shape model behavior at training time but are difficult to modify post-deployment and cannot be
independently audited by the harness. A distinct approach externalizes governance rules into deployment-
| time configuration |     | that           | the harness | can        | read, validate, | and         | enforce. |                 |            |         |
| ------------------ | --- | -------------- | ----------- | ---------- | --------------- | ----------- | -------- | --------------- | ---------- | ------- |
|                    |     |                |             |            |                 |             |          | The AutoHarness | repository | (AIMing |
| Deployment-time    |     | constitutions: |             | YAML-based |                 | governance. |          |                 |            |         |
Lab, 2026) encodes governance rules in a YAML file that specifies the pipeline mode (core, standard, or
enhanced), risk classification patterns, allowed and denied tool patterns, token budget limits, and audit
log destinations. This declarative style separates governance intent from execution logic. Non-developer
stakeholderssuchassecurityteamsandcomplianceofficerscanreviewandmodifypolicieswithouttouching
agent code. Unlike training-time constitutions, YAML files can be updated, versioned, and diffed with
standard tooling, enabling policy updates without retraining or redeploying the model.
The two layers differ operationally. Training-time constitutions are costly to modify and must be inferred
throughbehavioralprobes, whiledeployment-timeYAMLisdirectlyreadableanddiff-reviewable. Training-
time alignment shapes default behavior probabilistically and can be overridden by adversarial prompts (An-
driushchenko et al., 2024); deployment-time rules instead execute as harness checks.
Pattern-basedYAMLrulessufficewhenpoliciesreducetoliteraltriggers,butrealdeploymentsoftenrequire
conditional logic over runtime state. Current YAML schemas do not standardize predicates over privilege
escalation, host-based egress, session-level rate limits, or future actions. Between free-form YAML and
| hard-coded   | rules | lies a third | design     | point: | structured | policy | DSLs.         |                |                  |       |
| ------------ | ----- | ------------ | ---------- | ------ | ---------- | ------ | ------------- | -------------- | ---------------- | ----- |
|              |       |              |            |        | Progent’s  | policy | language (Shi | et al., 2025a) | supports boolean | pred- |
| Programmable |       | policy       | languages. |        |            |        |               |                |                  |       |
icates, quantifiers, and environment references. It provides formal expressiveness while remaining readable.
Formal-LLM(Lietal.,2024)goesfurtherbyencodingplanconstraintsaspushdownautomata. Thisformal-
ism can express sequential ordering constraints, prohibited tool combinations, and required approval gates
atspecificsteps. VeriSafeAgent(Leeetal.,2025)formalizesuserintentintoaDSLoverUIstatetransitions,
43

Under review as submission to TMLR
verifying that proposed GUI actions align with the user’s task before execution. YAML constitutions admit
ambiguity; formal specifications demand expertise.
Open challenges. Nowidelyadoptedstandardschemaexistsforagentconstitutions. Eachharnesstends
to define its own YAML structure, making policies non-portable. Tooling to validate that a constitution
is internally consistent (e.g., no contradictory allow/deny rules) and complete (e.g., no unhandled tool
categories)appearslimitedinthecurrentecosystem. Theinteractionbetweentraining-timeanddeployment-
timeconstitutionsisparticularlyunderexplored. WhetheraYAMLdeny-rulecanreliablyoverrideabehavior
thatRLHFhasreinforced,andunderwhatconditionsthetwolayersconflict,remainsanopenquestionwith
practical security implications.
9.5 Audit Infrastructure
Governance requires accountability. Audit infrastructure records what the agent did, why it did it, and
whether governance policies were respected. These records support post-hoc investigation, regulatory com-
pliance, and continuous policy refinement.
Structured audit trails. AutoHarness (AIMing Lab, 2026) emits per-tool-call JSONL records that in-
clude the tool name, arguments, risk classification, permission decision, execution result, token cost, and
wall-clock latency. These structured logs support both real-time dashboards and offline forensic analysis.
SAGA(Syrosetal.,2025)extendsaudittrailstomulti-agentinteractionsbyrecordingcryptographictokens
exchanged between agents, enabling provenance tracking across trust boundaries. Across these systems, a
replayableauditrecordneedsatleastatraceidentifier,principalidentity,toolinvocation,policydecisionand
version,executionresult,resourcecost,andanintegrityhashoverrelevantinputsandoutputs. Mostcurrent
systems record only a subset of these fields, and few sign or hash records, leaving audit trails susceptible to
log tampering by a compromised agent process.
Beyond recording, detecting governance violations in long-running agents requires automated analysis.
Anomaly detection: per-action versus trajectory level. Detectionmechanismssplitalongthegran-
ularity at which they evaluate evidence. Per-action detectors classify each tool call in isolation against a
learnedorspecifiednotionofrisk: inputandoutputguardrails(§9.2)operateinthisregime,andAgentMon-
itor (Naihin et al., 2023) provides a lightweight log-and-flag implementation. This regime is cheap and easy
toaudit, butitcannotrecognizeattacksthatdistributethemselvesacrossmanyindividuallybenignactions,
such as a slow exfiltration that reads one file per minute. Trajectory-level detectors evaluate sequences of
actions jointly. AgentAuditor (Luo et al., 2025) combines behavioral pattern matching with LLM-based
reasoning over full traces. SentinelAgent (He et al., 2025) models multi-agent communication as a temporal
graph and flags anomalous interaction patterns. Trajectory-level detection catches multi-step attacks at the
cost of higher latency and a less localized notion of which action triggered the alert, complicating both real-
time intervention and post-hoc explanation. In the systems surveyed here, per-action checks are typically
deployed inline, while trajectory-level analysis runs asynchronously over the audit log.
Beyond security, long-running agents also require cost and resource governance.
Cost and resource auditing. A runaway agent loop can exhaust API budgets quickly in loop-heavy
workloads. The2025OWASPTop10forLLMs(OWASPFoundation,2025)listsresourcedrainasadistinct
riskcategory. AutoHarness(AIMingLab,2026)tracksper-calltokenconsumptionandenforcessession-level
budgets declaratively through its constitution. Cost-aware governance matters especially in multi-agent
architectures where fan-out patterns can multiply API calls exponentially.
Tiered governance pipelines. An emerging design pattern integrates the preceding mechanisms (per-
missions, hooks, constitutions, and audit) into a single configurable pipeline. AutoHarness (AIMing Lab,
2026) exemplifies this pattern with three tiers. The tiers add progressively deeper checks, from parse–risk–
permission–execute–audit loops to context enrichment, output validation, anomaly scoring, human escala-
tion, and formal constraint verification. The tier is selected declaratively via the YAML constitution, so
44

| Under review | as submission | to TMLR |     |     |     |     |
| ------------ | ------------- | ------- | --- | --- | --- | --- |
governance overhead scales with deployment risk. Other production guidance exposes similar responsibili-
ties as feature-level controls rather than named tiers (Shavit et al., 2023). Which abstraction is more usable
| remains | an open empirical | question. |     |     |     |     |
| ------- | ----------------- | --------- | --- | --- | --- | --- |
Openchallenges. Auditlogsaccumulaterapidlyinlong-runningagents,raisingchallengesaroundstorage,
privacy, and signal-to-noise ratio. Logs may contain sensitive user data, API keys, or conversation content,
creating tension between audit completeness and data protection requirements. The community also lacks
standardized audit schemas, making cross-system analysis and regulatory reporting difficult.
| 9.6 Situating | Governance | in the Agent | Security | Landscape |     |     |
| ------------- | ---------- | ------------ | -------- | --------- | --- | --- |
Governance mechanisms respond to a concrete threat landscape. Recent evidence (Zhang et al., 2026b; Kim
et al., 2026; Chen et al., 2026; Wei et al., 2026) from open agent-to-agent platforms further suggests that
agent security is not limited to prompt injection or single-agent jailbreaks: social engineering, coordinated
agent clusters, credential leakage, and platform-level engagement amplification can jointly shape the threat
landscape. Kim et al. (2026) survey 128 papers and catalogue 51 attack methods and 60 defense meth-
ods across the agent stack. Chen et al. (2026) complement this with a software-engineering perspective,
synthesizing 50 papers through a six-dimensional taxonomy and proposing a reference doctrine for secure-
by-construction agent platforms. We use these frameworks to connect governance mechanisms to specific
| security | risks and identify | coverage gaps. |     |     |     |     |
| -------- | ------------------ | -------------- | --- | --- | --- | --- |
From design dimensions to governance mechanisms. Kim et al. identify seven design dimensions
(Input Trust, Access Sensitivity, Workflow, Action, Memory, Tool, User Interface), each representing a
flexibilityspectrum. Greaterflexibilityexpandstheattacksurface,andgovernanceconstrainsthatflexibility
at runtime. Permission models bound tools and actions; lifecycle hooks inject checkpoints into workflows;
constitutions externalize constraints; and audit infrastructure provides the feedback loop that reveals when
constraints are too loose or too tight. Table 3 maps governance mechanisms to the seven risk categories
| (R1–R7) | in Kim et | al.’s taxonomy. |     |     |     |     |
| ------- | --------- | --------------- | --- | --- | --- | --- |
Table 3: Mapping governance mechanisms to the risk taxonomy of Kim et al. (2026).
|     | Governance | Mechanism |     | Risks Mitigated | or  | Detected |
| --- | ---------- | --------- | --- | --------------- | --- | -------- |
Permission models and identity mgmt. R1 (untrusted interfaces), R5 (data leak-
|     |                  |            |     | age), R6 | (unauthorized      | actions)   |
| --- | ---------------- | ---------- | --- | -------- | ------------------ | ---------- |
|     | Input guardrails |            |     | R1, R2   | (wrong instruction | following) |
|     | Output           | guardrails |     | R2, R4   | (hallucination),   | R5, R6     |
Information flow control R3 (unconstrained data flow), R5, R6
|     | Component         | hardening    |     | R1, R2, | R4           |        |
| --- | ----------------- | ------------ | --- | ------- | ------------ | ------ |
|     | Monitoring        | and audit    |     | R5, R6, | R7 (resource | drain) |
|     | Human-in-the-loop |              |     | R2, R6  |              |        |
|     | Privilege         | separation   |     | R2, R3  |              |        |
|     | Formal            | verification |     | R2, R6  |              |        |
Declarative constitution Cross-cutting: configures all of the above
Defense gaps in real-world agents. Kim et al.’s case studies on six agent systems (Codex, Gemini
CLI, OpenHands, Browser Use, Nanobrowser, Skyvern) reveal that no agent fully implements all defense
categories. Information flow control, identity management, and formal verification are absent from every
surveyed system. In all six cases, monitoring is partial: agents log tool calls but lack automated anomaly
detection. TheAutoGPTcasestudyillustratestheconsequence: downstreampatchescanaddressindividual
symptoms while leaving upstream input validation, information flow control, and policy composition under-
specified.
45

| Under review     | as  | submission | to  | TMLR    |              |            |          |          |         |               |
| ---------------- | --- | ---------- | --- | ------- | ------------ | ---------- | -------- | -------- | ------- | ------------- |
|                  |     |            |     | Kim     | et al. argue | that agent | security | requires | layered | defenses that |
| Defense-in-depth |     | and        | its | limits. |              |            |          |          |         |               |
complement each other: input guardrails as first-line protection, output guardrails as last-line defense,
information flow control and monitoring as continuous runtime protection, access control for authentication
and authorization, and human-in-the-loop for critical decisions. However, layering is not free; as discussed
in §9.2, poorly coordinated layers may interfere with each other, and the composability of independent
governance hooks remains largely untested. In this framing, governance can serve as the orchestration layer
| that helps | defense | mechanisms |     | cooperate rather | than conflict. |     |     |     |     |     |
| ---------- | ------- | ---------- | --- | ---------------- | -------------- | --- | --- | --- | --- | --- |
Contextual security as a proposed extension. Kim et al. (2026) propose contextual security as a
candidatefourthsecuritygoalforagenticsystems,alongsidetheclassicalconfidentiality–integrity–availability
(CIA)triad. Theproposalisrecentandspecifictotheirsurvey;ithasnotbeenadoptedbystandardsbodies
such as the National Institute of Standards and Technology (NIST) or by mainstream security textbooks,
and we treat it here as a useful framing rather than as a settled definition. Conseca (Tsai & Bagdasarian,
2025) and CaMeL (Debenedetti et al., 2025) illustrate the engineering direction: context must be treated
as governed state rather than as passive prompt material. Whether this warrants elevation to a standalone
| security     | goal remains | unsettled. |     |     |     |     |     |     |     |     |
| ------------ | ------------ | ---------- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9.7 Research |              | Directions |     |     |     |     |     |     |     |     |
Table 4 summarizes the state of governance across the systems discussed in this section.
Table 4: Governance feature coverage. = full support, = partial, = absent.
|     |        |     |       |       | (cid:32) |          | (cid:71)(cid:35) |       | (cid:35)  |     |
| --- | ------ | --- | ----- | ----- | -------- | -------- | ---------------- | ----- | --------- | --- |
|     | System |     | Perm. | Hooks | Harden.  | Constit. |                  | Audit | Multi-Ag. |     |
Codex
Gemini CLI
|     |     |     |     | (cid:32) (cid:35)(cid:71) | (cid:35) |     | (cid:35) | (cid:35)(cid:71) | (cid:35) |     |
| --- | --- | --- | --- | ------------------------- | -------- | --- | -------- | ---------------- | -------- | --- |
OpenHands
|     |     |     |     | (cid:32) (cid:35)(cid:71) | (cid:35) |     | (cid:35) | (cid:35)(cid:71) | (cid:35) |     |
| --- | --- | --- | --- | ------------------------- | -------- | --- | -------- | ---------------- | -------- | --- |
AutoHarness
|     |     |     |     | (cid:35)(cid:71) (cid:32) | (cid:35) |     | (cid:35) | (cid:35)(cid:71) | (cid:35)(cid:71) |     |
| --- | --- | --- | --- | ------------------------- | -------- | --- | -------- | ---------------- | ---------------- | --- |
Progent
|     |     |     |     | (cid:32) (cid:32) | (cid:71)(cid:35) |     | (cid:32) | (cid:32) | (cid:35)(cid:71) |     |
| --- | --- | --- | --- | ----------------- | ---------------- | --- | -------- | -------- | ---------------- | --- |
CaMeL
|     |     |     |     | (cid:32) (cid:32) | (cid:35) |     | (cid:35)(cid:71) | (cid:35) | (cid:35) |     |
| --- | --- | --- | --- | ----------------- | -------- | --- | ---------------- | -------- | -------- | --- |
SAGA
|     |     |     |     | (cid:35)(cid:71) (cid:32) | (cid:35) |     | (cid:35) | (cid:35) | (cid:35) |     |
| --- | --- | --- | --- | ------------------------- | -------- | --- | -------- | -------- | -------- | --- |
IsolateGPT
|     |     |     |     | (cid:32) (cid:71)(cid:35) | (cid:35) |     | (cid:35) | (cid:32) | (cid:32) |     |
| --- | --- | --- | --- | ------------------------- | -------- | --- | -------- | -------- | -------- | --- |
AgentSpec
|     |     |     |     | (cid:32) (cid:71)(cid:35) | (cid:35) |     | (cid:35) | (cid:35) | (cid:32) |     |
| --- | --- | --- | --- | ------------------------- | -------- | --- | -------- | -------- | -------- | --- |
SAFEFLOW
|     |     |     |     | (cid:35)(cid:71) (cid:32) | (cid:35)         |     | (cid:32) | (cid:35) | (cid:35) |     |
| --- | --- | --- | --- | ------------------------- | ---------------- | --- | -------- | -------- | -------- | --- |
|     |     |     |     | (cid:35)(cid:71) (cid:32) | (cid:71)(cid:35) |     | (cid:35) | (cid:32) | (cid:32) |     |
The sparsity visible in Table 4 suggests that governance infrastructure is often a practical bottleneck for
safe deployment alongside model limitations. We identify eight open research directions, restricted here to
governance-specific gaps and cross-referenced with the broader open problems in §12.
|                  |     |        |     |                  | Each | harness | defines | its own | YAML | schema and pro- |
| ---------------- | --- | ------ | --- | ---------------- | ---- | ------- | ------- | ------- | ---- | --------------- |
| (1) Standardized |     | policy | and | audit languages. |      |         |         |         |      |                 |
prietary DSL, fragmenting the governance ecosystem. A community-driven specification, analogous to what
MCP (Anthropic, 2024c) is pursuing for tool interfaces, would enable portable policies, composable gover-
| nance modules, |     | and cross-harness |     | audit interoperability. |     |     |     |     |     |     |
| -------------- | --- | ----------------- | --- | ----------------------- | --- | --- | --- | --- | --- | --- |
(2) Formal governance guarantees. Current governance mechanisms remain limited in formal guaran-
tees. Formal verification of agent behavior remains at an early stage (Li et al., 2024; Chen et al., 2025b; Lee
et al.,2025). Extendingthese techniquesto verify governancepipeline correctness, for instance proving that
a constitution is internally consistent and covers all tool categories, remains underexplored.
(3) Adaptive governance. Static policies cannot anticipate every task context. Conseca (Tsai & Bag-
dasarian, 2025) demonstrates that LLM-generated policies can bridge this gap. The trustworthiness of
machine-generated governance rules, and the question of how such policy generators should themselves be
| governed, | remain | open. |     |     |     |     |     |     |     |     |
| --------- | ------ | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
46

| Under          | review | as submission | to TMLR      |         |        |              |     |            |     |           |                 |
| -------------- | ------ | ------------- | ------------ | ------- | ------ | ------------ | --- | ---------- | --- | --------- | --------------- |
|                |        |               |              |         | Agents | that execute |     | multi-hour | or  | multi-day | tasks introduce |
| (4) Governance |        | for           | long-horizon | agents. |        |              |     |            |     |           |                 |
contextdrift,session-spanningstate,andevolvingtrustassumptions. Manycurrentgovernancepipelinesare
designedforsingle-turnorshort-sessionagents. Scalingthemtolong-horizonautonomyrequiresgovernance
rules whose validity can be renewed, revoked, and audited over evolving sessions.
|            |            |     |             | Usable | governance | interfaces |     | are necessary |     | for deployment. | The field |
| ---------- | ---------- | --- | ----------- | ------ | ---------- | ---------- | --- | ------------- | --- | --------------- | --------- |
| (5) Usable | governance |     | interfaces. |        |            |            |     |               |     |                 |           |
needs human–computer interaction (HCI) research on permission UIs, audit dashboards, and constitution
editors that are accessible to non-specialist users. Prior work on mobile permissions suggests a risk that
approval dialogs will transfer poorly to the agentic setting (Felt et al., 2012), but agent-specific studies are
still needed.
|                 |     |            |            |     | Training-time | alignment |     | (constitutional |     | AI), | deployment-time |
| --------------- | --- | ---------- | ---------- | --- | ------------- | --------- | --- | --------------- | --- | ---- | --------------- |
| (6) Cross-layer |     | governance | coherence. |     |               |           |     |                 |     |      |                 |
configuration (YAML constitutions), and runtime enforcement (lifecycle hooks) operate at different layers
with different fidelities. How these layers compose, and whether runtime governance can reliably override
| training-time |     | dispositions, | remains | an open | question. |     |     |     |     |     |     |
| ------------- | --- | ------------- | ------- | ------- | --------- | --- | --- | --- | --- | --- | --- |
(7) End-to-end supply chain governance. MCP security extensions such as ETDI (Bhatt et al., 2025)
address tool integrity within a single harness. However, agents also depend on external packages, datasets,
and retrieval sources whose provenance is difficult to verify. Package hallucination attacks (Spracklen et al.,
2025) demonstrate that LLMs can inadvertently introduce supply chain compromises. Governance frame-
works that span the full tool and data supply chain, from package repository to agent execution, remain
limited.
(8)Unifiedadversarialbenchmarksforgovernancestacks. Existingbenchmarkstargetnarrowthreat
classes, such as prompt injection, trajectory diagnosis, or MCP server vulnerabilities (Debenedetti et al.,
2024; Liu et al., 2026a; Radosevich & Halloran, 2025). None evaluates a complete governance stack under a
common adversary model with reproducible attack traces. A community benchmark would need to report
defense effectiveness, false-positive rate, and overhead jointly rather than in isolation.
| 10 Cross-Cutting |     |     | Concerns |     |     |     |     |     |     |     |     |
| ---------------- | --- | --- | -------- | --- | --- | --- | --- | --- | --- | --- | --- |
The concerns collected in this section cut across multiple ETCLOVG layers and develop Claim 1 (the agent
harnessasanindependentsystemlayer,§1)byshowingwherelayer-specificreasoningbreaksdown. Thelayer
chapters isolate execution, tools, context, lifecycle, observability, evaluation, and governance so that each
design surface can be described precisely. Production harnesses, however, fail most often at the interfaces
| among       | these surfaces. |     |           |     |              |     |                  |     |     |           |             |
| ----------- | --------------- | --- | --------- | --- | ------------ | --- | ---------------- | --- | --- | --------- | ----------- |
|             |                 |     |           | The | seven layers | are | not independent. |     | The | execution | environment |
| Inter-layer | interaction     |     | patterns. |     |              |     |                  |     |     |           |             |
(E)constrainswhichlifecycleandorchestrationstrategies(L)arepractical; contextmanagement(C)affects
evaluation reproducibility (V); and governance (G) imposes identity, permission, and audit constraints that
span every other layer. A harness design should therefore be read as a dependency structure, not as a
| checklist | of separable |     | components. |     |     |     |     |     |     |     |     |
| --------- | ------------ | --- | ----------- | --- | --- | --- | --- | --- | --- | --- | --- |
Strongerevaluation(V),strictergovernance(G),richerobservability
| The cost–quality–speed |     |     | trilemma. |     |     |     |     |     |     |     |     |
| ---------------------- | --- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
(O),andmorefaithfulexecutionenvironments(E)generallyincreasecostandlatency. Optimizingforspeed
oftenreducesdiagnosticdepthorsafetymargin,whileoptimizingforqualitycanmakeiterationtooexpensive
forroutineuse. Realsystemsmustchoosewhichchecksaresynchronous,whichrunoffline,andwhichfailures
| justify         | costly | recovery | paths.    |           |           |      |     |           |     |     |                    |
| --------------- | ------ | -------- | --------- | --------- | --------- | ---- | --- | --------- | --- | --- | ------------------ |
|                 |        |          |           |           | Protocols | such | as  | MCP, ACP, | and | A2A | reflect a pressure |
| Standardization |        | and      | ecosystem | dynamics. |           |      |     |           |     |     |                    |
toward shared interfaces for tools, agents, and orchestration state. This pressure favors agent-agnostic
infrastructureoversingle-agentintegrations,butitalsoshiftsresponsibilitytogovernanceandobservability:
a standardized tool call is useful only if the surrounding harness can preserve provenance, permissions, cost,
| and failure | evidence | across | systems. |     |     |     |     |     |     |     |     |
| ----------- | -------- | ------ | -------- | --- | --- | --- | --- | --- | --- | --- | --- |
Persistent ecosystem gaps. Across the corpus, five gaps recur at layer boundaries: cross-tool interoper-
ability, cost attribution, failure recovery, multi-repository orchestration, and human-agent handoff. These
47

| Under review | as submission | to TMLR |     |     |
| ------------ | ------------- | ------- | --- | --- |
gaps motivate the synthesis in §11: the central question is no longer whether each layer has available tools,
| but whether    | the composed | harness behaves | as a reliable | control system. |
| -------------- | ------------ | --------------- | ------------- | --------------- |
| 11 Cross-Layer |              | Synthesis       |               |                 |
This section consolidates the cross-cutting concerns of §10 into five system-level effects and is the central
supportforClaim1(§1). Thepurposeistoshiftthediscussionfromcomponentcoveragetoharnessbehavior:
once execution, tools, context, orchestration, observability, evaluation, and governance are composed, their
| interactions            | create constraints | that no single | layer can | solve alone. |
| ----------------------- | ------------------ | -------------- | --------- | ------------ |
| 11.1 Cost-Quality-Speed |                    | Trilemma       |           |              |
Harness reliability is constrained by a three-way tradeoff between cost, quality, and speed. Stronger sand-
boxes and more faithful environments improve safety and reproducibility but increase startup latency and
infrastructure cost; richer context and memory policies can improve task continuity but consume tokens
and introduce retrieval overhead; deeper evaluation and observability improve diagnosis but slow iteration
and add storage, labeling, and trace-processing costs. Production systems therefore cannot treat quality
as a scalar objective. They must decide which risks justify expensive controls, which checks can run asyn-
chronouslyorinregressionsuites,andwhichtelemetryisworthcapturingateachstageoftheagentlifecycle.
| 11.2 Capability-Control |     | Tradeoff |     |     |
| ----------------------- | --- | -------- | --- | --- |
More capable harnesses expose more authority to the agent, but every increase in authority expands the
control problem. Larger tool menus broaden task coverage while increasing selection error and prompt-
injection surface; persistent memory helps long-running tasks but creates provenance, staleness, and privacy
risks;permissivesandboxesmakeautonomousexecutionusefulbutalsoenlargetheblastradiusofmisaligned
or compromised actions. The capability-control tradeoff is therefore not a security add-on to an otherwise
functional system. It is a design axis that links tool schemas, context policy, runtime permissions, identity,
| auditability, | and human | approval. |     |     |
| ------------- | --------- | --------- | --- | --- |
| 11.3 Harness  | Coupling  | Problem   |     |     |
Harnesslayersarecoupledinwaysthatmakelocaloptimizationfragile. Theexecutionenvironmentchanges
evaluation results by affecting package availability, reset semantics, latency, and failure modes; tool descrip-
tions consume context budget and shape model behavior; observability traces become governance evidence
only if identity and permission state are captured at the same granularity; and evaluation design feeds back
into orchestration by rewarding some recovery loops and penalizing others. These couplings imply that
harness changes should be tested as system changes. A prompt, tool, memory, sandbox, verifier, or monitor
may look beneficial in isolation while degrading the whole rollout when combined with the rest of the con-
trol loop. The coupling problem also explains why agent scores cannot be cleanly attributed to the model
without specifying the surrounding controller. Under the closed-loop framing, a change to context policy,
tool schema, verifier, or recovery loop changes the controller and therefore the measured behavior of the
C H
| same model | (Bölük, | 2026b).             |           |     |
| ---------- | ------- | ------------------- | --------- | --- |
| 11.4 From  | Agent   | Frameworks to Agent | Platforms |     |
The ecosystem is moving from agent frameworks toward agent platforms. Frameworks package local ab-
stractions such as agents, tools, memory stores, and execution loops; platforms add durable workspaces,
managed sandboxes, identity, billing, observability, evaluation, governance, and human handoff across many
runs and many users. This transition matters because long-running agents are no longer just programs that
call models. They are operational systems that need tenancy, compliance, fault recovery, trace retention,
andorganizationalownership. Asaresult,thecentraldesignquestionshiftsfrom“howdoIbuildanagent?”
to “how do I operate a fleet of agents whose actions remain inspectable and reversible over time?”
48

Under review as submission to TMLR
11.5 Open Research Agenda
The synthesis points to a research agenda centered on harnesses as adaptive control systems. The field
needs benchmarks that vary harness interventions rather than only model weights, trace-native methods
for attributing failures across layers, protocols for transferring state and responsibility among agents, tools,
sandboxes, evaluators, and humans, and optimization methods that simplify harnesses as models improve.
The next section turns these cross-layer effects into five open questions: how to harden and scale execution
environments,maintainreliablestate,diagnosefailuresfromtraces,standardizehandoffs,andkeepharnesses
useful under changing model capability.
12 Open Problems and Future Directions
The open problems collected here follow from the binding-constraint thesis and the cross-layer synthesis,
and they form the forward-looking part of the evidence for Claim 1 (§1). Rather than treating the seven
ETCLOVG layers as independent component lists, this section asks where the whole harness remains sci-
entifically under-specified. The central pattern is that agent harnesses are becoming long-running control
systems, but the field still lacks mature answers for hardening the execution substrate, preserving state,
diagnosing failures, transferring responsibility, and updating the harness as model capabilities change. We
organize these gaps into five questions that cut across the taxonomy.
12.1 Hardening and Scaling Execution Environments
Executionenvironmentsarebecomingthecontrolboundarywheresecurity,scalability,andportabilitymeet.
SandboxEscapeBenchdocumentsthatfrontiermodelscanexploitsandboxweaknessesunderrealisticconfig-
urations (Marchand et al., 2026), but defense work remains fragmented across systems with different threat
models and evaluation protocols (Wu et al., 2025; Yan, 2025). At the same time, the one-container-per-
task pattern strains large-scale training and evaluation, where tens of thousands of parallel trajectories need
cheap reset and replay; SWE-World points toward Docker-free surrogate environments, but the fidelity of
learned transitions relative to real execution remains unresolved (Sun et al., 2026). Even deployment porta-
bility is not a solved engineering detail: Docker-based sandboxes inherit Linux-kernel assumptions, while
macOS,Windows, browser, desktop, and hybrid-cloudsettings expose differentisolation andreproducibility
constraints.
The open problem is to make the runtime substrate both measurable and composable. Future harnesses
needcommonsecurityevaluationsforpromptinjection,goalmisalignment,andcompositionalamplification;
cost models that decide when to use containers, microVMs, OS-level permission boundaries, full desktop
VMs, browser environments, or learned surrogates; and portability layers that preserve semantics across
self-hosted, cloud, and hybrid deployments. The bundle-versus-compose split between framework-integrated
runtimes(§3.2.4)andsandboxabstractions(§3.2.7)shouldbetreatedasanempiricaldesignquestionrather
than a product preference. Standards such as MCP may reduce composition cost, but only if the tool,
governance,andobservabilitylayersexposeenoughstatetokeepruntimechoicesauditable,recoverable,and
safe.
12.2 Maintaining Reliable State in Long-Running Agents
The deepest context problem is not simply how to fit more tokens into a prompt, but how to keep an
agent’sworkingstatealignedwiththetruetaskstateoverlonghorizons. Long-runningcoding,research,and
operationsagentsrepeatedlysummarize,retrieve,compact,andexternalizeinformation;everysuchoperation
can delete constraints, distort priorities, or preserve stale assumptions. Recent context-engineering work
treats compaction, tool-result clearing, retrieval, and prompt-cache-aware ordering as practical mechanisms
formanaginglimitedcontextwindows(AnthropicAppliedAITeam,2025;Anthropic,2025c;OpenAI,2026b).
However, context rot and memory benchmarks show that longer inputs and richer memory stores do not
automatically imply better task-state tracking (Hong et al., 2025; Tan et al., 2025; He et al., 2026).
49

Under review as submission to TMLR
A principled research agenda should therefore recast context management as state estimation. The open
question is whether we can characterize how much task-relevant information is lost at each compression,
retrieval, or forgetting step, and whether we can bound the divergence between the agent’s internal state
and the real state of the task. Recent surveys formalize agent memory as a write–manage–read loop and
identify policy-learned management as an emerging mechanism family (Zhang et al., 2025; Du, 2026). Fu-
ture systems need uncertainty-aware summaries, provenance for remembered facts, contradiction handling,
explicit staleness markers, and recovery procedures that let an agent reconstruct missing state from durable
artifacts rather than trusting its own compressed history. This also suggests a tighter link between memory
and evaluation: memory policies should be judged not only by recall accuracy, but by whether they prevent
downstream action errors in multi-session tasks.
12.3 Diagnosing Failures from Agent Traces
Agent evaluation is still too often final-score-centric: a run passes or fails, and the final number is treated
as evidence about model quality. For harness engineering, this is insufficient because a failed rollout may
originate from model reasoning, a misleading tool schema, sandbox misconfiguration, stale context, flaky
tests, benchmark ambiguity, judge instability, or orchestration loops. Anthropic’s analysis of agentic coding
evaluations shows that infrastructure settings can measurably shift benchmark scores (Anthropic, 2026a),
and recent work on randomness in agentic evals argues that single-run pass rates can hide substantial vari-
ance (Bjarnason et al., 2026). The evaluation layer must therefore be studied as a measurement instrument,
not merely used as a leaderboard generator.
The next step is trace-native evaluation: traces should become the primary object from which systems
compute outcome scores, trajectory quality, failure attribution, and regression tests. Observability systems
alreadycapturespans,toolcalls,costs,retries,exceptions,andintermediatemessages(OpenTelemetry,2026;
AlSayyad et al., 2026; Koc et al., 2025), but these traces are often disconnected from evaluation pipelines.
LangChain’s 2026 survey reports that 89% of teams use observability while only 52.4% run offline evalu-
ations (LangChain, 2026a); this gap means teams can see what agents did without systematically judging
whether the behavior was correct. Future work should close this loop by converting anomalous production
traces into regression cases, computing trajectory metrics directly over spans, and feeding diagnostic sig-
nals back into prompt, tool, context, and orchestration changes. Reflexion showed that agents can learn
from their own traces in short-horizon settings (Shinn et al., 2023); extending this idea to long-running,
multi-session harnesses remains open.
12.4 Standard Handoffs Across Agents, Tools, and Humans
Modern harnesses increasingly distribute work across planners, subagents, tools, sandboxes, evaluators, and
humans, but the interfaces between these actors remain ad hoc. There are emerging local standards: MCP
standardizes tool access, A2A targets inter-agent communication, and OpenTelemetry provides a general
substrate for traces (Model Context Protocol, 2025b; A2A Project, 2025; OpenTelemetry, 2026; Ehtesham
et al., 2025). What is missing is a cross-layer handoff contract. When a planner hands work to an executor,
an agent calls a tool, a subagent returns control, or a system escalates to a human, the handoff should
transfer not only a text summary but also intent, constraints, permissions, artifacts, provenance, budget
state, risk level, trace history, and unresolved decisions.
This problem is partly technical and partly institutional. OpenAI’s Symphony frames the issue tracker
and repository as a control plane for agent work, while Anthropic’s long-running-agent harnesses emphasize
durable progress artifacts and clean handoff state (Kotliarskyi et al., 2026; Anthropic, 2025d; 2026b). Gov-
ernanceworkreachesthesameconclusionfromtheoppositedirection: agentidentity,delegation,permission
manifests, and auditability are needed before agents can safely act on behalf of users across systems (South
et al., 2025; Marro et al., 2025; Syros et al., 2025). The open problem is to define handoff protocols that
are rich enough for safety and recovery, but simple enough for broad adoption. Such protocols should make
responsibility explicit: who authorized the action, which state was transferred, which evidence supports the
currentplan, whatthereceiverisallowedtodo, andwhencontrolmustreturntoanotheragentorahuman.
50

Under review as submission to TMLR
12.5 Keeping Harnesses Useful as Models Improve
Harness design should not be assumed to move monotonically toward more scaffolding. Every wrapper,
reset, verifier, planner, memory rule, and permission gate encodes an assumption about what the model
cannot do reliably on its own. As model capabilities change, harness interventions should be re-estimated
ratherthanassumedtoremainbeneficial. Afactorialmodel-by-harnessevaluationcanrevealwhenaninter-
vention improves all models, helps only specific model families, or reverses model rankings (Bölük, 2026b).
Anthropicreportsaconcreteversionofthispatterninlong-runningapplicationdevelopment: contextresets
that were useful for one model became dispensable for a stronger model, and removing them reduced cost
without degrading quality (Anthropic, 2026c). OpenAI similarly frames harness engineering as a discipline
of keeping human attention, repository state, and agent execution aligned rather than merely adding more
scaffolding (OpenAI, 2026a;b).
This creates a meta-engineering agenda: harnesses need mechanisms for optimizing and simplifying them-
selves. Meta-Harness shows that prompts, tools, and control loops can be searched as part of the optimiza-
tion target rather than fixed by hand (Lee et al., 2026), while Natural-Language Agent Harnesses make
harnessmodulesexplicitandablatable(Panetal.,2026). Productionobservabilityandcostsystemssuchas
TensorZero, Axon, andAgentOpspointtowardbudget-awareharnessoperation(TensorZero,2026;harshke-
dia177, 2026; AgentOps AI, 2026), but the research problem is broader than cost minimization. Future
systems should identify which interventions are causally responsible for quality, safety, or reliability; run
shadow-mode or A/B tests across harness variants; and optimize under joint quality–latency–cost–risk con-
straints. A central risk is benchmark overfitting: a harness that optimizes itself only against a narrow suite
may become brittle. The more durable goal is adaptive simplification, where the harness continuously asks
which controls are still necessary as tasks, tools, and model capabilities change.
13 Conclusion
This survey treats the agent harness as an independent engineering surface and argues that infrastructure
quality, not model capability alone, sets the ceiling on real-world agent reliability. Around this binding-
constraint thesis we develop three claims. The seven-layer ETCLOVG taxonomy separates Observability
and Governance from Lifecycle Hooks and reflects how production teams already organize their tooling
and ownership. A mapping of 170+ open-source projects onto the taxonomy gives the most extensive
ecosystem snapshot to date and surfaces adoption patterns, coverage gaps, and emerging design principles.
A three-phase engineering evolution from prompt to context to harness engineering, together with a cross-
layer synthesis covering the cost–quality–speed trilemma, the capability–control tradeoff, and the harness
couplingproblem,situatestheharnesswithinabroaderengineeringtrajectory. Ouranalysishaslimits. The
corpusisbiasedtowardEnglish-language,GitHub-visible,open-sourceprojects,andtowardthecoding-agent
ecosystem; extending it to closed-source production systems and to non-coding agent ecosystems would
sharpen the empirical picture. The taxonomy itself is descriptive: turning ETCLOVG into a normative
framework that can guide harness design decisions, rather than only classify them, is the natural next step
we hope this survey will encourage.
51

| Under review | as  | submission | to  | TMLR |     |     |     |     |
| ------------ | --- | ---------- | --- | ---- | --- | --- | --- | --- |
References
A2A Project. Agent2agent (A2A) protocol. GitHub repository, 2025. URL https://github.com/
| a2aproject/A2A. |     | Accessed |     | May 14, 2026. |     |     |     |     |
| --------------- | --- | -------- | --- | ------------- | --- | --- | --- | --- |
General Action. Emdash. https://github.com/generalaction/emdash, 2026. GitHub repository.
Aden. Openhive: Multi-agent swarms deployed in minutes for long-session business process.
https://
| github.com/aden-hive/hive, |     |     |     | 2026. | GitHub | repository. |     |     |
| -------------------------- | --- | --- | --- | ----- | ------ | ----------- | --- | --- |
affaan-m. everything-claude-code. https://github.com/affaan-m/everything-claude-code, 2025.
| GitHub | repository. |     |     |     |     |     |     |     |
| ------ | ----------- | --- | --- | --- | --- | --- | --- | --- |
Alexandru Agache, Marc Brooker, Alexandra Iordache, Anthony Liguori, Rolf Neugebauer, Phil Piwonka,
andDiana-MariaPopa.Firecracker: Lightweightvirtualizationforserverlessapplications.In17thUSENIX
symposium on networked systems design and implementation (NSDI 20), pp. 419–434, 2020.
Agent Infra. agent-infra sandbox: All-in-one sandbox for AI agents. https://github.com/agent-infra/
| sandbox, | 2024. | Open-source |     | software. |     |     |     |     |
| -------- | ----- | ----------- | --- | --------- | --- | --- | --- | --- |
agentmd. AGENT.md: The universal agent configuration file. GitHub repository, 2025. URL
https:
| //github.com/agentmd/agent.md. |     |     |     | Accessed |     | May 14, | 2026. |     |
| ------------------------------ | --- | --- | --- | -------- | --- | ------- | ----- | --- |
AgentOps AI. AgentOps: Python SDK for AI agent monitoring, LLM cost tracking, benchmarking, and
| observability. |     | https://github.com/AgentOps-AI/agentops, |     |     |     |     | 2026. |     |
| -------------- | --- | ---------------------------------------- | --- | --- | --- | --- | ----- | --- |
agentsmd. AGENTS.md. GitHub repository, 2025. URL https://github.com/agentsmd/agents.md. Ac-
| cessed May | 14, | 2026. |     |     |     |     |     |     |
| ---------- | --- | ----- | --- | --- | --- | --- | --- | --- |
Aider-AI. aider: Ai pair programming in your terminal. https://github.com/aider-ai/aider, 2025.
| GitHub | repository. |     |     |     |     |     |     |     |
| ------ | ----------- | --- | --- | --- | --- | --- | --- | --- |
AIMing Lab. AutoHarness: Automated harness engineering for AI agents. https://github.com/
| aiming-lab/AutoHarness, |     |     |     | 2026. Version | 0.1.0, | released | April 1, | 2026. |
| ----------------------- | --- | --- | --- | ------------- | ------ | -------- | -------- | ----- |
Ken Aizawa. Writing effective tools for agents – with agents. Anthropic Engineering Blog, September 2025.
URL https://www.anthropic.com/engineering/writing-tools-for-agents.
Alibaba. OpenSandbox: A general-purpose sandbox platform for AI applications. https://github.com/
| alibaba/OpenSandbox, |     |     | 2026. | Open-source | software. |     |     |     |
| -------------------- | --- | --- | ----- | ----------- | --------- | --- | --- | --- |
Adam AlSayyad, Kelvin Yuxiang Huang, and Richik Pal. Agenttrace: A structured logging framework
for agent system observability. In LLM-based Multi-Agent Systems: Towards Responsible, Reliable, and
| Scalable | Agentic | Systems, | 2026. |     |     |     |     |     |
| -------- | ------- | -------- | ----- | --- | --- | --- | --- | --- |
Maksym Andriushchenko, Francesco Croce, and Nicolas Flammarion. Jailbreaking leading safety-aligned
| llms with | simple | adaptive | attacks. |       |          | arXiv:2404.02151, |     | 2024. |
| --------- | ------ | -------- | -------- | ----- | -------- | ----------------- | --- | ----- |
|           |        |          |          | arXiv | preprint |                   |     |       |
Anomaly. Opencode: The open source ai coding agent. https://github.com/anomalyco/opencode, 2025.
| GitHub | repository. |     |     |     |     |     |     |     |
| ------ | ----------- | --- | --- | --- | --- | --- | --- | --- |
Anthropic. Building effective agents. Anthropic Engineering Blog, December 2024a. URL https://www.
anthropic.com/engineering/building-effective-agents.
Anthropic. Introducing computer use, a new Claude 3.5 Sonnet, and Claude 3.5 Haiku.
https://www.
| anthropic.com/news/3-5-models-and-computer-use, |     |     |     |     |     |     | 2024b. Blog | post. |
| ----------------------------------------------- | --- | --- | --- | --- | --- | --- | ----------- | ----- |
Anthropic. Introducing the model context protocol. https://www.anthropic.com/news/
| model-context-protocol, |     |     |     | November | 2024c. |     |     |     |
| ----------------------- | --- | --- | --- | -------- | ------ | --- | --- | --- |
Anthropic. Claude code. https://github.com/anthropics/claude-code, 2025. GitHub repository.
52

| Under review | as  | submission | to TMLR |     |     |     |     |     |     |
| ------------ | --- | ---------- | ------- | --- | --- | --- | --- | --- | --- |
Anthropic. Claude Code documentation. https://docs.claude.com/en/docs/claude-code/overview,
| 2025a. | Documentation. |     |     |     |     |     |     |     |     |
| ------ | -------------- | --- | --- | --- | --- | --- | --- | --- | --- |
Anthropic. Beyondpermissionprompts: MakingClaudeCodemoresecureandautonomous. https://www.
anthropic.com/engineering/claude-code-sandboxing, October 2025b. Blog post.
Anthropic. Context management: Tool result clearing and compaction. https://www.anthropic.com/
| news/context-management, |     |     | 2025c. |     | News | article. |     |     |     |
| ------------------------ | --- | --- | ------ | --- | ---- | -------- | --- | --- | --- |
Anthropic. Effective harnesses for long-running agents. Anthropic Engineering Blog, 2025d. URL
https://
www.anthropic.com/engineering/effective-harnesses-for-long-running-agents. Accessed May
14, 2026.
Anthropic. How we built our multi-agent research system. https://www.anthropic.com/engineering/
| multi-agent-research-system, |     |     |     | 2025e. | Blog | post. |     |     |     |
| ---------------------------- | --- | --- | --- | ------ | ---- | ----- | --- | --- | --- |
Anthropic. Code execution with MCP: Building more efficient AI agents. Anthropic Engineering Blog,
November 2025f. URL https://www.anthropic.com/engineering/code-execution-with-mcp. Ac-
| cessed | May 14, | 2026. |     |     |     |     |     |     |     |
| ------ | ------- | ----- | --- | --- | --- | --- | --- | --- | --- |
Anthropic. Anthropic sandbox runtime: A lightweight sandboxing tool for enforcing filesystem and network
restrictions at the OS level. https://github.com/anthropic-experimental/sandbox-runtime, 2025g.
| Research | preview | and | npm package |     | anthropic-ai/sandbox-runtime. |     |     |     |     |
| -------- | ------- | --- | ----------- | --- | ----------------------------- | --- | --- | --- | --- |
Anthropic. Claude’s constitution. https://www.anthropic.com/constitution, January 2026a. Published
| January | 22, 2026; | released | under | CC0 | 1.0. |     |     |     |     |
| ------- | --------- | -------- | ----- | --- | ---- | --- | --- | --- | --- |
Anthropic. Demystifying evals for AI agents. https://www.anthropic.com/engineering/
| demystifying-evals-for-ai-agents, |         |        |     |              | 2026b. | Engineering |     | blog.        |     |
| --------------------------------- | ------- | ------ | --- | ------------ | ------ | ----------- | --- | ------------ | --- |
| Anthropic.                        | Harness | design | for | long-running |        | application |     | development. |     |
https://www.anthropic.com/
| engineering/harness-design-long-running-apps, |     |     |     |     |     |     | 2026c. | Blog | post. |
| --------------------------------------------- | --- | --- | --- | --- | --- | --- | ------ | ---- | ----- |
Anthropic. Quantifying infrastructure noise in agentic coding evals. Anthropic Engineering Blog, 2026a.
URL https://www.anthropic.com/engineering/infrastructure-noise.
Anthropic. Scaling managed agents: Decoupling the brain from the hands. Anthropic Engineering Blog,
| 2026b. | URL https://www.anthropic.com/engineering/managed-agents. |     |     |     |     |     |     |     |     |
| ------ | --------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
Anthropic Applied AI Team. Effective context engineering for AI agents. https://www.anthropic.com/
engineering/effective-context-engineering-for-ai-agents, 2025. Blog post.
Arize AI. OpenInference: OpenTelemetry-based auto-instrumentation and semantic conventions for AI
| applications. |     | https://github.com/Arize-ai/openinference, |     |     |     |     |     |     | 2026a. |
| ------------- | --- | ------------------------------------------ | --- | --- | --- | --- | --- | --- | ------ |
Arize AI. Phoenix: AI observability and evaluation. https://github.com/Arize-ai/phoenix, 2026b.
Hammad Atta, Muhammad Zeeshan Baig, Yasir Mehmood, Nadeem Shahzad, Ken Huang, Muhammad
Aziz Ul Haq, Muhammad Awais, and Kamal Ahmed. Qsaf: A novel mitigation framework for cognitive
| degradation | in  | agentic | ai.   |          | arXiv:2507.15330, |     |     | 2025. |     |
| ----------- | --- | ------- | ----- | -------- | ----------------- | --- | --- | ----- | --- |
|             |     |         | arXiv | preprint |                   |     |     |       |     |
Lei Ba, Qinbin Li, and Songze Li. Ciber: A comprehensive benchmark for security evaluation of code
| interpreter | agents. | arXiv | preprint | arXiv:2602.19547, |     |     | 2026. |     |     |
| ----------- | ------- | ----- | -------- | ----------------- | --- | --- | ----- | --- | --- |
Fu Bang. Gptcache: An open-source semantic cache for llm applications enabling faster answers and cost
savings. InProceedingsofthe3rdWorkshopforNaturalLanguageProcessingOpenSourceSoftware(NLP-
| 2023), | pp. | 212–218, | 2023. |     |     |     |     |     |     |
| ------ | --- | -------- | ----- | --- | --- | --- | --- | --- | --- |
OSS
Manish Bhatt, Vineeth Sai Narajala, and Idan Habler. Etdi: Mitigating tool squatting and rug pull attacks
inmodelcontextprotocol(mcp)byusingoauth-enhancedtooldefinitionsandpolicy-basedaccesscontrol.
In 2025 Cyber Awareness and Research Symposium (CARS), pp. 1–6. IEEE, 2025.
53

| Under | review | as submission | to TMLR |     |     |     |     |     |     |
| ----- | ------ | ------------- | ------- | --- | --- | --- | --- | --- | --- |
StellaBiderman,HaileySchoelkopf,LintangSutawika,LeoGao,JonathanTow,BaberAbbasi,AlhamFikri
Aji, Pawan Sasanka Ammanamanchi, Sidney Black, Jordan Clive, et al. Lessons from the trenches on
reproducible evaluation of language models. arXiv:2405.14782, 2024.
arXiv preprint
Bjarni Haukur Bjarnason, André Silva, and Martin Monperrus. On randomness in agentic evals. arXiv
|     | arXiv:2602.07150, |     | 2026. | URL | https://arxiv.org/abs/2602.07150. |     |     |     |     |
| --- | ----------------- | --- | ----- | --- | --------------------------------- | --- | --- | --- | --- |
preprint
Bloop-AI. Vibe-kanban. https://github.com/BloopAI/vibe-kanban, 2026. GitHub repository.
Birgitta Böckeler. Harness engineering for coding agent users. Martin Fowler website, April 2026. URL
https://martinfowler.com/articles/harness-engineering.html.
Léo Boisvert, Megh Thakkar, Maxime Gasse, Massimo Caccia, Thibault L De Chezelles, Quentin Cappart,
Nicolas Chapados, Alexandre Lacoste, and Alexandre Drouin. Workarena++: Towards compositional
planningandreasoning-basedcommonknowledgeworktasks.
|          |               |     |       |     |     | Advances |     | in Neural Information | Processing |
| -------- | ------------- | --- | ----- | --- | --- | -------- | --- | --------------------- | ---------- |
| Systems, | 37:5996–6051, |     | 2024. |     |     |          |     |                       |            |
Can Bölük. I improved 15 LLMs at coding in one afternoon. Only the harness changed., February 2026a.
URL https://blog.can.ac/2026/02/12/the-harness-problem/.
Can Bölük. I improved 15 LLMs at coding in one afternoon. Only the harness changed. https://blog.
| can.ac/2026/02/12/the-harness-problem/, |     |     |     |     | 2026b. Blog | post. |     |     |     |
| --------------------------------------- | --- | --- | --- | --- | ----------- | ----- | --- | --- | --- |
Hugo Bowne-Anderson and Jeff Huber. Harness engineering: Why agent context isn’t enough.
https:
//hugobowne.substack.com/p/harness-engineering-why-agent-context, 2026. Blog post.
Christoph Bühler, Matteo Biagiola, Luca Di Grazia, and Guido Salvaneschi. Securing ai agent execution.
| arXiv | preprint | arXiv:2510.21236, |     | 2025. |     |     |     |     |     |
| ----- | -------- | ----------------- | --- | ----- | --- | --- | --- | --- | --- |
Bytedance. Deerflow - 2.0. https://github.com/bytedance/deer-flow, 2026. GitHub repository.
MertCemri,MelissaZPan,ShuyiYang,LakshyaAAgrawal,BhavyaChopra,RishabhTiwari,KurtKeutzer,
Aditya Parameswaran, Dan Klein, Kannan Ramchandran, et al. Why do multi-agent llm systems fail?
|     |     | arXiv:2503.13657, |     | 2025. |     |     |     |     |     |
| --- | --- | ----------------- | --- | ----- | --- | --- | --- | --- | --- |
arXiv preprint
LingjiaoChen, MateiZaharia, andJamesZou. Frugalgpt: Howtouselargelanguagemodelswhilereducing
| cost | and improving | performance. |     | arXiv | preprint arXiv:2305.05176, |     | 2023. |     |     |
| ---- | ------------- | ------------ | --- | ----- | -------------------------- | --- | ----- | --- | --- |
Shiping Chen, Qin Wang, Guangsheng Yu, Xu Wang, and Liming Zhu. Clawed and dangerous: Can we
| trust | open | agentic systems? | arXiv | preprint | arXiv:2603.26221, | 2026. |     |     |     |
| ----- | ---- | ---------------- | ----- | -------- | ----------------- | ----- | --- | --- | --- |
Sizhe Chen, Arman Zharmagambetov, Saeed Mahloujifar, Kamalika Chaudhuri, David Wagner, and Chuan
Guo. Secalign: Defending against prompt injection with preference optimization. In
Proceedings of the
2025 ACM SIGSAC Conference on Computer and Communications Security, pp. 2833–2847, 2025a.
ZhaorunChen,MintongKang,andBoLi.Shieldagent: Shieldingagentsviaverifiablesafetypolicyreasoning.
| arXiv | preprint | arXiv:2503.22738, |     | 2025b. |     |     |     |     |     |
| ----- | -------- | ----------------- | --- | ------ | --- | --- | --- | --- | --- |
Daixuan Cheng, Shaohan Huang, Yuxian Gu, Huatong Song, Guoxin Chen, Li Dong, Wayne Xin Zhao,
Ji-Rong Wen, and Furu Wei. Llm-in-sandbox elicits general agentic intelligence.
arXiv preprint
| arXiv:2601.16206, |     | 2026. |     |     |     |     |     |     |     |
| ----------------- | --- | ----- | --- | --- | --- | --- | --- | --- | --- |
DeChezelles, ThibaultLeSellier, SaharOmidiShayegan, LawrenceKeunhoJang, XingHanLù, OriYoran,
Dehan Kong, Frank F Xu, Siva Reddy, Quentin Cappart, et al. The browsergym ecosystem for web agent
| research. |     |     | arXiv:2412.05467, |     | 2024. |     |     |     |     |
| --------- | --- | --- | ----------------- | --- | ----- | --- | --- | --- | --- |
arXiv preprint
Prateek Chhikara, Dev Khant, Saket Aryan, Taranjeet Singh, and Deshraj Yadav. Mem0: Building
production-ready ai agents with scalable long-term memory. arXiv preprint arXiv:2504.19413, 2025.
HongcheolCho,RyangkyungKang,andYoungeunKim. SkillRet: Alarge-scalebenchmarkforskillretrieval
in LLM agents. arXiv preprint arXiv:2605.05726, 2026. URL https://arxiv.org/abs/2605.05726.
54

| Under review | as submission | to TMLR |     |     |     |     |     |
| ------------ | ------------- | ------- | --- | --- | --- | --- | --- |
CometML.Opik: Open-sourceLLMevaluation,observability,andoptimizationplatform.
https://github.
| com/comet-ml/opik, |     | 2026. |     |     |     |     |     |
| ------------------ | --- | ----- | --- | --- | --- | --- | --- |
ConfidentAI. DeepEval: TheLLMevaluationframework. https://github.com/confident-ai/deepeval,
| 2026. Open-source | software. |     |     |     |     |     |     |
| ----------------- | --------- | --- | --- | --- | --- | --- | --- |
context-space. context-space: Context engineering infrastructure. https://github.com/context-space/
| context-space, | 2025. | GitHub repository. |     |     |     |     |     |
| -------------- | ----- | ------------------ | --- | --- | --- | --- | --- |
Cua. Cua: Open-source infrastructure for computer-use agents. https://github.com/trycua/cua, 2024.
| Open-source | software. |     |     |     |     |     |     |
| ----------- | --------- | --- | --- | --- | --- | --- | --- |
Daytona Platforms, Inc. Daytona: Secure and elastic infrastructure for running AI-generated code. https:
| //github.com/daytonaio/daytona, |     |     | 2024. | Open-source | software. |     |     |
| ------------------------------- | --- | --- | ----- | ----------- | --------- | --- | --- |
EdoardoDebenedetti,JieZhang,MislavBalunovic,LucaBeurer-Kellner,MarcFischer,andFlorianTramèr.
Agentdojo: A dynamic environment to evaluate prompt injection attacks and defenses for llm agents.
|          |                       |     |            | Systems, | 37:82895–82920, | 2024. |     |
| -------- | --------------------- | --- | ---------- | -------- | --------------- | ----- | --- |
| Advances | in Neural Information |     | Processing |          |                 |       |     |
Edoardo Debenedetti, Ilia Shumailov, Tianqi Fan, Jamie Hayes, Nicholas Carlini, Daniel Fabian, Christoph
Kern, Chongyang Shi, Andreas Terzis, and Florian Tramèr. Defeating prompt injections by design. arXiv
|     | arXiv:2503.18813, | 2025. |     |     |     |     |     |
| --- | ----------------- | ----- | --- | --- | --- | --- | --- |
preprint
Peng Ding. ToolRegistry: A protocol-agnostic tool management library for function-calling LLMs. arXiv
preprint arXiv:2507.10593, 2025. URL https://arxiv.org/abs/2507.10593.
| Docker, Inc. | Docker sandboxes: | A new | approach | for coding | agent | safety. |     |
| ------------ | ----------------- | ----- | -------- | ---------- | ----- | ------- | --- |
https://www.docker.com/blog/
docker-sandboxes-a-new-approach-for-coding-agent-safety/, 2025. Blog post.
HermanZvonimirDošilović.Judge0: Robust,fast,scalable,andsandboxedopen-sourceonlinecodeexecution
| system. | https://github.com/judge0/judge0, |     |     | 2024. | Open-source | software. |     |
| ------- | --------------------------------- | --- | --- | ----- | ----------- | --------- | --- |
Alexandre Drouin, Maxime Gasse, Massimo Caccia, Issam H Laradji, Manuel Del Verme, Tom Marty, Léo
Boisvert,MeghThakkar,QuentinCappart,DavidVazquez,etal. Workarena: Howcapablearewebagents
at solving common knowledge work tasks? arXiv:2403.07718, 2024.
|     |     |     |     | arXiv preprint |     |     |     |
| --- | --- | --- | --- | -------------- | --- | --- | --- |
Pengfei Du. Memory for autonomous llm agents: Mechanisms, evaluation, and emerging frontiers.
arXiv
| preprint | arXiv:2603.07670, | 2026. |     |     |     |     |     |
| -------- | ----------------- | ----- | --- | --- | --- | --- | --- |
Yu Du, Fangyun Wei, and Hongyang Zhang. Anytool: Self-reflective, hierarchical agents for large-scale API
calls. InProceedings of the 41st International Conference on Machine Learning,volume235ofProceedings
of Machine Learning Research, pp. 11812–11829. PMLR, 2024. URL https://proceedings.mlr.press/
v235/du24h.html.
E2B. E2B: Code interpreting for AI apps. GitHub repository, 2024. URL https://github.com/e2b-dev/
| E2B. Accessed | May 14, | 2026. |     |     |     |     |     |
| ------------- | ------- | ----- | --- | --- | --- | --- | --- |
Abul Ehtesham, Aditi Singh, Gaurav Kumar Gupta, and Saket Kumar. A survey of agent interoperability
protocols: Model context protocol (MCP), agent communication protocol (ACP), agent-to-agent protocol
(A2A),andagentnetworkprotocol(ANP). arXivpreprintarXiv:2505.02279,2025. URLhttps://arxiv.
org/abs/2505.02279.
Shahul Es, Jithin James, Luis Espinosa Anke, and Steven Schockaert. Ragas: Automated evaluation of
retrieval augmented generation. In Proceedings of the 18th conference of the european chapter of the
|             |                   |              |        | demonstrations, |     | pp. 150–158, | 2024. |
| ----------- | ----------------- | ------------ | ------ | --------------- | --- | ------------ | ----- |
| association | for computational | linguistics: | system |                 |     |              |       |
Xiang Fei, Xiawu Zheng, and Hao Feng. MCP-zero: Active tool discovery for autonomous LLM agents.
arXiv preprint arXiv:2506.01056, 2025. URL https://arxiv.org/abs/2506.01056.
55

| Under review | as submission | to TMLR |     |     |     |     |     |     |
| ------------ | ------------- | ------- | --- | --- | --- | --- | --- | --- |
Adrienne Porter Felt, Elizabeth Ha, Serge Egelman, Ariel Haney, Erika Chin, and David Wagner. Android
permissions: User attention, comprehension, and behavior. In Proceedings of the eighth symposium on
|                | security, | pp. 1–14, | 2012. |     |     |     |     |     |
| -------------- | --------- | --------- | ----- | --- | --- | --- | --- | --- |
| usable privacy | and       |           |       |     |     |     |     |     |
LeoGao,JonathanTow,StellaBiderman,SidBlack,AnthonyDiPofi,CharlesFoster,LaurenceGolding,Jef-
freyHsu,KyleMcDonell,NiklasMuennighoff,etal. Aframeworkforfew-shotlanguagemodelevaluation.
| Zenodo, | 2021. |     |     |     |     |     |     |     |
| ------- | ----- | --- | --- | --- | --- | --- | --- | --- |
Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yixin Dai, Jiawei Sun, Haofen
Wang, Haofen Wang, et al. Retrieval-augmented generation for large language models: A survey. arXiv
|     | arXiv:2312.10997, | 2(1):32, | 2023. |     |     |     |     |     |
| --- | ----------------- | -------- | ----- | --- | --- | --- | --- | --- |
preprint
GitHub. Github agentic workflows. https://github.com/github/gh-aw, 2026. GitHub repository.
GitHub. Searching for repositories. https://docs.github.com/en/search-github/
searching-on-github/searching-for-repositories, 2026. GitHub Docs, accessed April 29,
2026.
Google. gVisor: Thecontainersecurityplatform. https://github.com/google/gvisor,2018. Open-source
software.
Google. Gemini cli: An open-source ai agent that brings the power of gemini directly into your terminal.
https://github.com/google-gemini/gemini-cli, 2025. GitHub repository.
Kai Greshake, Sahar Abdelnabi, Shailesh Mishra, Christoph Endres, Thorsten Holz, and Mario Fritz. Not
what you’ve signed up for: Compromising real-world llm-integrated applications with indirect prompt
| injection. | In          |             |     |             |                         |     | security, | pp. 79–90, |
| ---------- | ----------- | ----------- | --- | ----------- | ----------------------- | --- | --------- | ---------- |
|            | Proceedings | of the 16th | ACM | workshop on | artificial intelligence | and |           |            |
2023.
Jiawei Gu, Xuhui Jiang, Zhichao Shi, Hexiang Tan, Xuehao Zhai, Chengjin Xu, Wei Li, Yinghan Shen,
Shengjie Ma, Honghao Liu, et al. A survey on llm-as-a-judge. Innovation, 2024.
The
Zhicheng Guo, Sijie Cheng, Hao Wang, Shihao Liang, Yujia Qin, Peng Li, Zhiyuan Liu, Maosong Sun, and
Yang Liu. StableToolBench: Towards stable large-scale benchmarking on tool learning of large language
| models. | In       |                    |     |               |              |     | 2024, pp. 11143–11156, |     |
| ------- | -------- | ------------------ | --- | ------------- | ------------ | --- | ---------------------- | --- |
|         | Findings | of the Association | for | Computational | Linguistics: | ACL |                        |     |
Bangkok, Thailand, 2024. Association for Computational Linguistics. doi: 10.18653/v1/2024.findings-acl.
| 664. URL | https://aclanthology.org/2024.findings-acl.664/. |     |     |     |     |     |     |     |
| -------- | ------------------------------------------------ | --- | --- | --- | --- | --- | --- | --- |
Tingxu Han, Zhenting Wang, Chunrong Fang, Shiyu Zhao, Shiqing Ma, and Zhenyu Chen. Token-budget-
awarellmreasoning. InFindings of the Association for Computational Linguistics: ACL 2025,pp.24842–
| 24855, 2025. |     |     |     |     |     |     |     |     |
| ------------ | --- | --- | --- | --- | --- | --- | --- | --- |
Shibo Hao, Tianyang Liu, Zhen Wang, and Zhiting Hu. ToolkenGPT: Augmenting frozen language
models with massive tools via tool embeddings. Advances in Neural Information Processing Sys-
tems,36:45870–45894,2023. URLhttps://proceedings.neurips.cc/paper_files/paper/2023/hash/
8fd1a81c882cd45f64958da6284f4a3f-Abstract-Conference.html.
harshkedia177. Axon. https://github.com/harshkedia177/axon, 2026. GitHub repository.
Xu He, Di Wu, Yan Zhai, and Kun Sun. Sentinelagent: Graph-based anomaly detection in multi-agent
| systems. |     | arXiv:2505.24201, | 2025. |     |     |     |     |     |
| -------- | --- | ----------------- | ----- | --- | --- | --- | --- | --- |
arXiv preprint
Zexue He, Yu Wang, Churan Zhi, Yuanzhe Hu, Tzu-Ping Chen, Lang Yin, Ze Chen, Tong Arthur Wu, Siru
Ouyang, Zihan Wang, et al. Memoryarena: Benchmarking agent memory in interdependent multi-session
| agentic | tasks. | arXiv:2602.16313, |     | 2026. |     |     |     |     |
| ------- | ------ | ----------------- | --- | ----- | --- | --- | --- | --- |
arXiv preprint
Helicone. Helicone: Open-source LLM observability platform for developers. https://github.com/
| Helicone/helicone, |     | 2026. |     |     |     |     |     |     |
| ------------------ | --- | ----- | --- | --- | --- | --- | --- | --- |
56

| Under review | as submission | to  | TMLR |     |     |     |     |     |     |
| ------------ | ------------- | --- | ---- | --- | --- | --- | --- | --- | --- |
Yeachan Heo. oh-my-claudecode. https://github.com/yeachan-heo/oh-my-claudecode, 2026. GitHub
repository.
Kelly Hong, Anton Troynikov, and Jeff Huber. Context rot: How increasing input tokens impacts llm
| performance, | 2025. |     |     |     |     |     |     |     |     |
| ------------ | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
SiruiHong, MingchenZhuge,JonathanChen,XiawuZheng, YuhengCheng,JinlinWang,CeyaoZhang, Zili
Wang,StevenKaShingYau,ZijuanLin,etal.Metagpt: Metaprogrammingforamulti-agentcollaborative
| framework. | In          |               |     |            |     |             | representations, | 2023. |     |
| ---------- | ----------- | ------------- | --- | ---------- | --- | ----------- | ---------------- | ----- | --- |
|            | The twelfth | international |     | conference |     | on learning |                  |       |     |
Ruida Hu, Chao Peng, Xinchen Wang, Junjielong Xu, and Cuiyun Gao. Repo2run: Automated building
executable environment for code repository at scale. arXiv preprint arXiv:2502.13681, 2025a.
Yuanzhe Hu, Yu Wang, and Julian McAuley. Evaluating memory in llm agents via incremental multi-turn
| interactions. | arXiv preprint |     | arXiv:2507.05257, |     | 2025b. |     |     |     |     |
| ------------- | -------------- | --- | ----------------- | --- | ------ | --- | --- | --- | --- |
Yue Huang, Jiawen Shi, Yuan Li, Chenrui Fan, Siyuan Wu, Qihui Zhang, Yixin Liu, Pan Zhou, Yao Wan,
NeilZhenqiangGong,andLichaoSun. MetaToolbenchmarkforlargelanguagemodels: Decidingwhether
to use tools and which to use. arXiv preprint arXiv:2310.03128, 2023. URL https://arxiv.org/abs/
2310.03128.
HuggingFace.huggingface/smolagents.GitHubrepository,2026.URLhttps://github.com/huggingface/
| smolagents. | Accessed | May | 14, 2026. |     |     |     |     |     |     |
| ----------- | -------- | --- | --------- | --- | --- | --- | --- | --- | --- |
HakanInan,KartikeyaUpasani,JianfengChi,RashiRungta,KrithikaIyer,YuningMao,MichaelTontchev,
Qing Hu, Brian Fuller, Davide Testuggine, et al. Llama guard: Llm-based input-output safeguard for
| human-ai | conversations. | arXiv | preprint | arXiv:2312.06674, |     | 2023. |     |     |     |
| -------- | -------------- | ----- | -------- | ----------------- | --- | ----- | --- | --- | --- |
Dennis Jacob, Hend Alzahrani, Zhanhao Hu, Basel Alomair, and David Wagner. Promptshield: Deployable
| detection   | for prompt | injection    | attacks. | In       |             |     |               |                |             |
| ----------- | ---------- | ------------ | -------- | -------- | ----------- | --- | ------------- | -------------- | ----------- |
|             |            |              |          |          | Proceedings | of  | the Fifteenth | ACM Conference | on Data and |
| Application | Security   | and Privacy, | pp.      | 341–352, | 2024.       |     |               |                |             |
NamanJain,JaskiratSingh,ManishShetty,LiangZheng,KoushikSen,andIonStoica.R2e-gym: Procedural
environments and hybrid verifiers for scaling open-weights swe agents. arXiv:2504.07164,
|     |     |     |     |     |     |     |     | arXiv preprint |     |
| --- | --- | --- | --- | --- | --- | --- | --- | -------------- | --- |
2025.
Rishi Jha, Harold Triedman, Justin Wagle, and Vitaly Shmatikov. Breaking and fixing defenses against
control-flow hijacking in multi-agent systems. arXiv:2510.17276, 2025.
|     |     |     |     |     | arXiv | preprint |     |     |     |
| --- | --- | --- | --- | --- | ----- | -------- | --- | --- | --- |
MenglinJia,LumingTang,Bor-ChunChen,ClaireCardie,SergeBelongie,BharathHariharan,andSer-Nam
Lim. Visual prompt tuning. In European conference on computer vision, pp. 709–727. Springer, 2022.
Carlos E Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, and Karthik
Narasimhan. Swe-bench: Can language models resolve real-world github issues? In 12th International
| Conference | on Learning | Representations, |     | ICLR | 2024, | 2024. |     |     |     |
| ---------- | ----------- | ---------------- | --- | ---- | ----- | ----- | --- | --- | --- |
Sayash Kapoor, Benedikt Stroebl, Peter Kirgis, Nitya Nadgir, Zachary S Siegel, Boyi Wei, Tianci Xue, Ziru
Chen,FelixChen,SaitejaUtpala,etal. Holisticagentleaderboard: Themissinginfrastructureforaiagent
| evaluation. | arXiv preprint | arXiv:2510.11977, |     |     | 2025. |     |     |     |     |
| ----------- | -------------- | ----------------- | --- | --- | ----- | --- | --- | --- | --- |
Andrej Karpathy. Context engineering. https://x.com/karpathy/status/1937902205765607626, 2025.
X post.
Kata Containers Project. Kata Containers: The speed of containers, the security of VMs. https:
//katacontainers.io/, 2017. Open-source OCI-compatible runtime using lightweight VMs.
JuheeKim,XiaoyuanLiu,ZhunWang,ShiQiu,BoLi,WenboGuo,andDawnSong. Theattackanddefense
landscape of agentic ai: A comprehensive survey. arXiv preprint arXiv:2603.11088, 2026.
57

| Under review | as  | submission | to  | TMLR |     |     |     |     |     |     |     |
| ------------ | --- | ---------- | --- | ---- | --- | --- | --- | --- | --- | --- | --- |
Sehoon Kim, Suhong Moon, Ryan Tabrizi, Nicholas Lee, Michael W. Mahoney, Kurt Keutzer, and Amir
Gholami. An LLM compiler for parallel function calling. In Proceedings of the 41st International Confer-
|         |         | Learning, |                                                 | volume | 235 | of          |     |            |          | Research, | pp. 24370–24391. |
| ------- | ------- | --------- | ----------------------------------------------- | ------ | --- | ----------- | --- | ---------- | -------- | --------- | ---------------- |
| ence on | Machine |           |                                                 |        |     | Proceedings |     | of Machine | Learning |           |                  |
| PMLR,   | 2024.   | URL       | https://proceedings.mlr.press/v235/kim24y.html. |        |     |             |     |            |          |           |                  |
David Kimai. Context-engineering: A first-principles handbook. https://github.com/davidkimai/
| Context-Engineering, |     |     | 2025. | GitHub | repository. |     |     |     |     |     |     |
| -------------------- | --- | --- | ----- | ------ | ----------- | --- | --- | --- | --- | --- | --- |
VincentKoc,JacquesVerre,DouglasBlank,andAbigailMorgan. Mindthemetrics: Patternsfortelemetry-
aware in-IDE AI application development using the model context protocol (MCP).
arXiv preprint
arXiv:2506.11019, 2025. URL https://arxiv.org/abs/2506.11019. arXiv:2506.11019.
Jing Yu Koh, Robert Lo, Lawrence Jang, Vikram Duvvur, Ming Lim, Po-Yu Huang, Graham Neubig,
Shuyan Zhou, Russ Salakhutdinov, and Daniel Fried. Visualwebarena: Evaluating multimodal agents on
| realisticvisualwebtasks. |         |     | InProceedings |          |     |             |        |         |        |             |                   |
| ------------------------ | ------- | --- | ------------- | -------- | --- | ----------- | ------ | ------- | ------ | ----------- | ----------------- |
|                          |         |     |               |          |     | of the 62nd | Annual | Meeting | of the | Association | for Computational |
| Linguistics              | (Volume |     | 1: Long       | Papers), | pp. | 881–905,    | 2024.  |         |        |             |                   |
Alex Kotliarskyi, Victor Zhu, and Zach Brock. An open-source spec for Codex orchestration: Symphony.
https://openai.com/index/open-source-codex-orchestration-symphony/, April 2026. OpenAI en-
| gineering | blog. |     |     |     |     |     |     |     |     |     |     |
| --------- | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Muratcan Koylan. Agent skills for context engineering. https://github.com/muratcankoylan/
| Agent-Skills-for-Context-Engineering, |     |     |     |     |     | 2025. | GitHub | repository. |     |     |     |
| ------------------------------------- | --- | --- | --- | --- | --- | ----- | ------ | ----------- | --- | --- | --- |
Kubernetes SIG Apps. agent-sandbox: A Kubernetes CRD and controller for isolated, stateful, singleton
workloads. https://github.com/kubernetes-sigs/agent-sandbox, 2025. Open-source software.
Laminar AI. Laminar (lmnr): Open-source observability platform purpose-built for AI agents.
https:
| //github.com/lmnr-ai/lmnr, |     |     |     | 2026. |     |     |     |     |     |     |     |
| -------------------------- | --- | --- | --- | ----- | --- | --- | --- | --- | --- | --- | --- |
LangChain. Evaluating deep agents: Our learnings. LangChain Blog, December 2025a. URL https:
//www.langchain.com/blog/evaluating-deep-agents-our-learnings.
| LangChain. |     | Evaluating |     | deep | agents: | Our | learnings. |     |     |     |     |
| ---------- | --- | ---------- | --- | ---- | ------- | --- | ---------- | --- | --- | --- | --- |
https://www.langchain.com/blog/
evaluating-deep-agents-our-learnings, December 2025b. Engineering blog.
LangChain. langchain-sandbox: Safely run untrusted Python code using Pyodide and Deno. https://
github.com/langchain-ai/langchain-sandbox, 2025c. Open-source software.
LangChain. Langgraph: Low-level orchestration framework for building stateful agents. https://github.
| com/langchain-ai/langgraph, |     |     |     | 2026a. | GitHub |     | repository. |     |     |     |     |
| --------------------------- | --- | --- | --- | ------ | ------ | --- | ----------- | --- | --- | --- | --- |
LangChain. deepagents. https://github.com/langchain-ai/deepagents, 2026b. GitHub repository.
LangChain. State of agent engineering. https://www.langchain.com/state-of-agent-engineering,
| 2026a. | Survey | report. |     |     |     |     |     |     |     |     |     |
| ------ | ------ | ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
LangChain. The anatomy of an agent harness. https://www.langchain.com/blog/
| the-anatomy-of-an-agent-harness, |     |     |     |     | 2026b. | Blog | post. |     |     |     |     |
| -------------------------------- | --- | --- | --- | --- | ------ | ---- | ----- | --- | --- | --- | --- |
LangChain. langchain-ai/langchain. GitHub repository, 2026c. URL https://github.com/langchain-ai/
| langchain. | Accessed |     | May 14, | 2026. |     |     |     |     |     |     |     |
| ---------- | -------- | --- | ------- | ----- | --- | --- | --- | --- | --- | --- | --- |
Langfuse. Langfuse: Open source LLM engineering platform. https://github.com/langfuse/langfuse,
2026.
Jungjae Lee, Dongjae Lee, Chihun Choi, Youngmin Im, Jaeyoung Wi, Kihong Heo, Sangeun Oh, Sunjae
Lee, and Insik Shin. Verisafe agent: Safeguarding mobile gui agent via logic-based action verification.
In Proceedings of the 31st Annual International Conference on Mobile Computing and Networking, pp.
| 817–831, | 2025. |     |     |     |     |     |     |     |     |     |     |
| -------- | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
58

| Under review | as submission | to TMLR |     |
| ------------ | ------------- | ------- | --- |
YoonhoLee,RoshenNair,QizhengZhang,KangwookLee,OmarKhattab,andChelseaFinn. Meta-harness:
End-to-end optimization of model harnesses. arXiv preprint arXiv:2603.28052, 2026.
GuohaoLi,HasanHammoud,HaniItani,DmitriiKhizbullin,andBernardGhanem. Camel: Communicative
agents for" mind" exploration of large language model society. Advances in neural information processing
| systems, | 36:51991–52008, | 2023a. |     |
| -------- | --------------- | ------ | --- |
Minghao Li, Yingxiu Zhao, Bowen Yu, Feifan Song, Hangyu Li, Haiyang Yu, Zhoujun Li, Fei Huang,
and Yongbin Li. API-bank: A comprehensive benchmark for tool-augmented LLMs. In Proceedings of
the 2023 Conference on Empirical Methods in Natural Language Processing, pp. 3102–3116, Singapore,
2023b. Association for Computational Linguistics. doi: 10.18653/v1/2023.emnlp-main.187. URL
https:
//aclanthology.org/2023.emnlp-main.187/.
Peiran Li, Xinkai Zou, Zhuohang Wu, Ruifeng Li, Shuo Xing, Hanwen Zheng, Zhikai Hu, Yuping Wang,
Haoxi Li, Qin Yuan, et al. Safeflow: A principled protocol for trustworthy and transactional autonomous
| agent systems. | arXiv | preprint arXiv:2506.07564, | 2025. |
| -------------- | ----- | -------------------------- | ----- |
Zelong Li, Wenyue Hua, Hao Wang, He Zhu, and Yongfeng Zhang. Formal-llm: Integrating formal language
and natural language for controllable llm-based agents. arXiv preprint arXiv:2402.00798, 2024.
Dongrui Liu, Qihan Ren, Chen Qian, Shuai Shao, Yuejin Xie, Yu Li, Zhonghao Yang, Haoyu Luo, Peng
Wang, Qingyu Liu, et al. Agentdog: A diagnostic guardrail framework for ai agent safety and security.
|     | arXiv:2601.18491, | 2026a. |     |
| --- | ----------------- | ------ | --- |
arXiv preprint
Nelson F Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy
Liang. Lost in the middle: How language models use long contexts. Transactions of the association for
|     | linguistics, | 12:157–173, 2024. |     |
| --- | ------------ | ----------------- | --- |
computational
XiaoLiu,HaoYu,HanchenZhang,YifanXu,XuanyuLei,HanyuLai,YuGu,HangliangDing,KaiwenMen,
Kejuan Yang, et al. Agentbench: Evaluating llms as agents. arXiv:2308.03688, 2023a.
arXiv preprint
Xunzhuo Liu, Bowei He, Xue Liu, Andy Luo, Haichen Zhang, and Huamin Chen. Dual-pool token-budget
routing for cost-efficient and reliable llm serving. arXiv preprint arXiv:2604.08075, 2026b.
YangLiu,DanIter,YichongXu,ShuohangWang,RuochenXu,andChenguangZhu. G-eval: Nlgevaluation
using gpt-4 with better human alignment. In Proceedings of the 2023 conference on empirical methods in
|         | processing, | pp. 2511–2522, | 2023b. |
| ------- | ----------- | -------------- | ------ |
| natural | language    |                |        |
Yupei Liu, Yuqi Jia, Jinyuan Jia, Dawn Song, and Neil Zhenqiang Gong. Datasentinel: A game-theoretic
detection of prompt injection attacks. In 2025 IEEE Symposium on Security and Privacy (SP), pp.
| 2190–2208. | IEEE, 2025. |     |     |
| ---------- | ----------- | --- | --- |
Jiaying Lu, Bo Pan, Jieyi Chen, Yingchaojie Feng, Jingyuan Hu, Yuchen Peng, and Wei Chen. Agentlens:
Visualanalysisforagentbehaviorsinllm-basedautonomoussystems.
IEEETransactionsonVisualization
| and Computer | Graphics, | 2024. |     |
| ------------ | --------- | ----- | --- |
Hanjun Luo, Shenyu Dai, Chiming Ni, Xinfeng Li, Guibin Zhang, Kun Wang, Tongliang Liu, and Hanan
Salam. Agentauditor: Human-level safety and security evaluation for llm agents. arXiv preprint
| arXiv:2506.00641, | 2025. |     |     |
| ----------------- | ----- | --- | --- |
Manus Team. Context engineering for AI agents: Lessons from building manus.
https://manus.im/blog/
Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus, 2025. Blog post.
RahulMarchand,ArtOCathain,JeromeWynne,PhilipposMaximosGiavridis,SamDeverett,JohnWilkin-
son,JasonGwartz,andHarryCoppock. Quantifyingfrontierllmcapabilitiesforcontainersandboxescape.
|     | arXiv:2603.02277, | 2026. |     |
| --- | ----------------- | ----- | --- |
arXiv preprint
SamueleMarro,AlanChan,XinxingRen,LewisHammond,JesseWright,GurjyotWanga,TizianoPiccardi,
Nuno Campos, Tobin South, Jialin Yu, et al. Permission manifests for web agents. arXiv preprint
| arXiv:2601.02371, | 2025. |     |     |
| ----------------- | ----- | --- | --- |
59

| Under review | as  | submission | to TMLR |     |     |     |     |     |     |     |
| ------------ | --- | ---------- | ------- | --- | --- | --- | --- | --- | --- | --- |
Meirtz. Awesome context engineering. https://github.com/Meirtz/Awesome-Context-Engineering,
| 2025. GitHub |     | repository. |     |     |     |     |     |     |     |     |
| ------------ | --- | ----------- | --- | --- | --- | --- | --- | --- | --- | --- |
Qianyu Meng, Yanan Wang, Liyi Chen, Qimeng Wang, Chengqiang Lu, Wei Wu, Yan Gao, Yi Wu, and Yao
Hu. Agent harness for large language model agents: A survey. Preprints, 2026.
Mike A Merrill, Alexander G Shaw, Nicholas Carlini, Boxuan Li, Harsh Raj, Ivan Bercovich, Lin Shi,
Jeong Yeon Shin, Thomas Walshe, E Kelly Buchanan, et al. Terminal-bench: Benchmarking agents on
hard, realistic tasks in command line interfaces. arXiv preprint arXiv:2601.11868, 2026.
GrégoireMialon,ClémentineFourrier,ThomasWolf,YannLeCun,andThomasScialom. Gaia: abenchmark
| for general | ai  | assistants. | In  |         |               |     |            |             | Representations, | 2023. |
| ----------- | --- | ----------- | --- | ------- | ------------- | --- | ---------- | ----------- | ---------------- | ----- |
|             |     |             | The | Twelfth | International |     | Conference | on Learning |                  |       |
Microsoft. Autogen. https://github.com/microsoft/autogen, 2025. GitHub repository.
Microsoft. Semantic kernel. https://github.com/microsoft/semantic-kernel, 2026. GitHub repository.
Microsoft. microsoft/semantic-kernel. GitHub repository, 2026. URL https://github.com/microsoft/
| semantic-kernel. |     | Accessed |     | May 14, | 2026. |     |     |     |     |     |
| ---------------- | --- | -------- | --- | ------- | ----- | --- | --- | --- | --- | --- |
mindfold-ai.Trellis: Multi-platformcoding-agentworkflowframework.https://github.com/mindfold-ai/
| Trellis, | 2025. | GitHub | repository. |     |     |     |     |     |     |     |
| -------- | ----- | ------ | ----------- | --- | --- | --- | --- | --- | --- | --- |
MLflow.MLflow: Anopen-sourceplatformforthemachinelearninglifecycle.https://github.com/mlflow/
| mlflow, | 2026. |     |     |     |     |     |     |     |     |     |
| ------- | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ModalLabs. Modal: ServerlesscloudplatformforAIanddataworkloads. https://modal.com,2024. Cloud
platform.
Model Context Protocol. modelcontextprotocol/servers. GitHub repository, 2025a. URL
https://github.
| com/modelcontextprotocol/servers. |     |     |     |     | Accessed | May | 14, | 2026. |     |     |
| --------------------------------- | --- | --- | --- | --- | -------- | --- | --- | ----- | --- | --- |
Model Context Protocol. Model context protocol specification (2025-06-18). Specification, 2025b. URL
https://modelcontextprotocol.io/specification/2025-06-18. Version 2025-06-18; accessed May
14, 2026.
Model Context Protocol. modelcontextprotocol/modelcontextprotocol. GitHub repository, 2025c. URL
https://github.com/modelcontextprotocol/modelcontextprotocol. Accessed May 14, 2026.
Dany Moshkovich and Sergey Zeltyn. Taming uncertainty via automation: Observing, analyzing, and opti-
| mizing | agentic | ai systems. |       |          | arXiv:2507.11277, |     |     | 2025. |     |     |
| ------ | ------- | ----------- | ----- | -------- | ----------------- | --- | --- | ----- | --- | --- |
|        |         |             | arXiv | preprint |                   |     |     |       |     |     |
Dany Moshkovich, Hadar Mulian, Sergey Zeltyn, Natti Eder, Inna Skarbovsky, and Roy Abitbol. Beyond
black-box benchmarking: Observability, analytics, and optimization of agentic systems. arXiv preprint
| arXiv:2503.06745, |     | 2025. |     |     |     |     |     |     |     |     |
| ----------------- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
Mozilla AI. cq: An open standard for shared agent learning. https://github.com/mozilla-ai/cq, 2025.
| GitHub | repository. |     |     |     |     |     |     |     |     |     |
| ------ | ----------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Hadar Mulian, Sergey Zeltyn, Ido Levy, Liane Galanti, Avi Yaeli, and Segev Shlomov. Agentfixer: From
failure detection to fix recommendations in llm agentic systems. arXiv preprint arXiv:2603.29848, 2026.
Taylor Mullen and Ryan J. Salva. Gemini CLI: An open-source AI agent that brings Gemini into
| your terminal. |     | Google | Blog, | June | 2025. | URL |     |     |     |     |
| -------------- | --- | ------ | ----- | ---- | ----- | --- | --- | --- | --- | --- |
https://blog.google/technology/developers/
introducing-gemini-cli-open-source-ai-agent/. Software: https://github.com/google-gemini/
gemini-cli.
Silen Naihin, David Atkinson, Marc Green, Merwane Hamadi, Craig Swift, Douglas Schonholtz, Adam Tau-
man Kalai, and David Bau. Testing language model agents safely in the wild. arXiv preprint
| arXiv:2311.10538, |     | 2023. |     |     |     |     |     |     |     |     |
| ----------------- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
60

| Under review | as submission |     | to TMLR |     |     |     |     |     |
| ------------ | ------------- | --- | ------- | --- | --- | --- | --- | --- |
YoheiNakajima. BabyAGI. GitHubrepository,2023. URLhttps://github.com/yoheinakajima/babyagi.
Milad Nasr, Nicholas Carlini, Chawin Sitawarin, Sander V Schulhoff, Jamie Hayes, Michael Ilie, Juliette
Pluto,ShuangSong,HarshChaudhari,IliaShumailov,etal.Theattackermovessecond: Strongeradaptive
attacks bypass defenses against llm jailbreaks and prompt injections. arXiv preprint arXiv:2510.09023,
2025.
Northflank. Northflank: Deploymicroservices,jobs,anddatabases. https://northflank.com,2024. Cloud
platform.
NVIDIA. Sandboxing agentic AI workflows with WebAssembly. https://developer.nvidia.com/blog/
sandboxing-agentic-ai-workflows-with-webassembly/, December 2024. Blog post.
OpenAI. Code interpreter: Allow models to write and run Python in a sandboxed environment.
https:
//platform.openai.com/docs/guides/tools-code-interpreter, 2023. API documentation.
OpenAI. Codex: Lightweightcodingagentthatrunsinyourterminal. https://github.com/openai/codex,
| 2025. GitHub | repository. |     |     |     |     |     |     |     |
| ------------ | ----------- | --- | --- | --- | --- | --- | --- | --- |
OpenAI. Introducing codex. OpenAI Blog, May 2025. URL https://openai.com/index/
introducing-codex/.
OpenAI. Openaiagentssdk. https://github.com/openai/openai-agents-python,2026a. GitHubrepos-
itory.
OpenAI. Symphony. https://github.com/openai/symphony, 2026b. GitHub repository.
| OpenAI. | Harness engineering: |     | leveraging |     | Codex | in  | an agent-first | world. |
| ------- | -------------------- | --- | ---------- | --- | ----- | --- | -------------- | ------ |
https://openai.com/index/
| harness-engineering, |     | 2026a. | Blog | post. |     |     |     |     |
| -------------------- | --- | ------ | ---- | ----- | --- | --- | --- | --- |
OpenAI. Unrolling the codex agent loop. https://openai.com/index/
| unrolling-the-codex-agent-loop, |                   |        |     | 2026b. |                | Blog post. |        |     |
| ------------------------------- | ----------------- | ------ | --- | ------ | -------------- | ---------- | ------ | --- |
| OpenAI.                         | Function calling. | OpenAI |     | API    | Documentation, |            | 2026c. | URL |
https://developers.openai.com/
| api/docs/guides/function-calling. |     |     |     |     | Accessed | May | 14, 2026. |     |
| --------------------------------- | --- | --- | --- | --- | -------- | --- | --------- | --- |
OpenAPI Initiative. OAI/OpenAPI-specification. GitHub repository, 2025. URL
https://github.com/
| OAI/OpenAPI-Specification. |     |     | Accessed |     | May | 14, 2026. |     |     |
| -------------------------- | --- | --- | -------- | --- | --- | --------- | --- | --- |
OpenTelemetry. OpenTelemetry: High-quality, ubiquitous, and portable telemetry to enable effective ob-
| servability. | https://github.com/open-telemetry, |     |     |            |     |            | 2026.     |     |
| ------------ | ---------------------------------- | --- | --- | ---------- | --- | ---------- | --------- | --- |
| OthmanAdi.   | planning-with-files:               |     |     | Persistent |     | file-based | planning. |     |
https://github.com/OthmanAdi/
| planning-with-files, |     | 2025. | GitHub |     | repository. |     |     |     |
| -------------------- | --- | ----- | ------ | --- | ----------- | --- | --- | --- |
OWASP Foundation. OWASP top 10 for large language model applications 2025.
https://owasp.org/
| www-project-top-10-for-large-language-model-applications/, |     |     |     |     |     |     |     | 2025. |
| ---------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | ----- |
CharlesPacker,VivianFang,Shishir_GPatil,KevinLin,SarahWooders,andJoseph_EGonzalez.Memgpt:
| towards | llms as operating |     | systems. | arXiv, | 2023. |     |     |     |
| ------- | ----------------- | --- | -------- | ------ | ----- | --- | --- | --- |
MatthewJPage,JoanneEMcKenzie,PatrickMBossuyt,IsabelleBoutron,TammyCHoffmann,CynthiaD
Mulrow, Larissa Shamseer, Jennifer M Tetzlaff, Elie A Akl, Sue E Brennan, et al. The prisma 2020
statement: an updated guideline for reporting systematic reviews. bmj, 372, 2021.
Linyue Pan, Lexiao Zou, Shuo Guo, Jingchen Ni, and Hai-Tao Zheng. Natural-language agent harnesses.
|     | arXiv:2603.25723, |     |     | 2026. |     |     |     |     |
| --- | ----------------- | --- | --- | ----- | --- | --- | --- | --- |
arXiv preprint
Joon Sung Park, Joseph O’Brien, Carrie Jun Cai, Meredith Ringel Morris, Percy Liang, and Michael S
Bernstein. Generativeagents: Interactivesimulacraofhumanbehavior. InProceedings of the 36th annual
| acm symposium | on  | user interface |     | software | and | technology, | pp. | 1–22, 2023. |
| ------------- | --- | -------------- | --- | -------- | --- | ----------- | --- | ----------- |
61

| Under review |     | as submission | to  | TMLR |     |     |     |
| ------------ | --- | ------------- | --- | ---- | --- | --- | --- |
Shishir G Patil, Tianjun Zhang, Vivian Fang, Roy Huang, Aaron Hao, Martin Casado, Joseph E Gonzalez,
Raluca Ada Popa, Ion Stoica, et al. Goex: Perspectives and designs towards a runtime for autonomous
| llm applications. |     |       |          | arXiv:2404.06921, |     | 2024a. |     |
| ----------------- | --- | ----- | -------- | ----------------- | --- | ------ | --- |
|                   |     | arXiv | preprint |                   |     |        |     |
Shishir G. Patil, Tianjun Zhang, Xin Wang, and Joseph E. Gonzalez. Gorilla: Large language
model connected with massive APIs. Advances in Neural Information Processing Systems, 37:
| 126544–126565, |     | 2024b. |     | URL |     |     |     |
| -------------- | --- | ------ | --- | --- | --- | --- | --- |
https://proceedings.neurips.cc/paper_files/paper/2024/hash/
e4c61f578ff07830f5c37378dd3ecb0d-Abstract-Conference.html.
Shishir G. Patil, Huanzhi Mao, Fanjia Yan, Charlie Cheng-Jie Ji, Vishnu Suresh, Ion Stoica, and Joseph E.
Gonzalez. The berkeley function calling leaderboard (BFCL): From tool use to agentic evaluation of large
languagemodels. InProceedingsofthe42ndInternationalConferenceonMachineLearning,volume267of
Proceedings of Machine Learning Research, pp. 48371–48392. PMLR, 2025. URL
https://proceedings.
mlr.press/v267/patil25a.html.
Plastic Labs. Honcho: Memory library for building stateful agents. https://github.com/plastic-labs/
| honcho, | 2025. | GitHub | repository. |     |     |     |     |
| ------- | ----- | ------ | ----------- | --- | --- | --- | --- |
Prime Intellect. verifiers: RL environments, evaluations, and agent harnesses for language models.
https:
//github.com/PrimeIntellect-ai/verifiers, 2026. Open-source software. Accessed: 2026-05-06.
| promptfoo | contributors. |     | Promptfoo: |     | LLM evals | and | red teaming. |
| --------- | ------------- | --- | ---------- | --- | --------- | --- | ------------ |
https://github.com/promptfoo/
| promptfoo, |     | 2026. Open-source |     | software. |     |     |     |
| ---------- | --- | ----------------- | --- | --------- | --- | --- | --- |
Pyodide Contributors. Pyodide: Python with the scientific stack, compiled to WebAssembly. https:
| //pyodide.org/, |     | 2018. | Open-source |     | software. |     |     |
| --------------- | --- | ----- | ----------- | --- | --------- | --- | --- |
ChenQian,WeiLiu,HongzhangLiu,NuoChen,YufanDang,JiahaoLi,ChengYang,WeizeChen,Yusheng
Su, Xin Cong, Juyuan Xu, Dahai Li, Zhiyuan Liu, and Maosong Sun. ChatDev: Communicative agents
forsoftwaredevelopment. arXiv:2307.07924,2023a. URLhttps://arxiv.org/abs/2307.
arXiv preprint
07924.
Cheng Qian, Chi Han, Yi R. Fung, Yujia Qin, Zhiyuan Liu, and Heng Ji. CREATOR: Tool creation for
disentanglingabstractandconcretereasoningoflargelanguagemodels. InFindings
of the Association for
Computational Linguistics: EMNLP 2023, pp. 6922–6939, Singapore, 2023b. Association for Computa-
| tional | Linguistics. | doi: | 10.18653/v1/2023.findings-emnlp.462. |     |     |     | URL |
| ------ | ------------ | ---- | ------------------------------------ | --- | --- | --- | --- |
https://aclanthology.org/2023.
findings-emnlp.462/.
Yujia Qin, Shihao Liang, Yining Ye, Kunlun Zhu, Lan Yan, Yaxi Lu, Yankai Lin, Xin Cong, Xiangru
Tang, Bill Qian, Sihan Zhao, Lauren Hong, Runchu Tian, Ruobing Xie, Jie Zhou, Mark Gerstein, Dahai
Li, Zhiyuan Liu, and Maosong Sun. ToolLLM: Facilitating large language models to master 16000+
real-world APIs. In The Twelfth International Conference on Learning Representations, 2024. URL
https://openreview.net/forum?id=dHng2O0Jjr.
Brandon Radosevich and John Halloran. Mcp safety audit: Llms with the model context protocol allow
| major | security | exploits. |     |     | arXiv:2504.03767, |     | 2025. |
| ----- | -------- | --------- | --- | --- | ----------------- | --- | ----- |
arXiv preprint
RagaAI. RagaAI-Catalyst: Python SDK for agent AI observability, monitoring, and evaluation.
https:
| //github.com/raga-ai-hub/RagaAI-Catalyst, |     |     |     |     |     | 2026. |     |
| ----------------------------------------- | --- | --- | --- | --- | --- | ----- | --- |
Benjamin Rombaut, Sogol Masoumzadeh, Kirill Vasilevski, Dayi Lin, and Ahmed E Hassan. Watson: A
cognitive observability framework for the reasoning of llm-powered agents. In 2025 40th IEEE/ACM
International Conference on Automated Software Engineering (ASE), pp. 739–751. IEEE, 2025.
AymericRoucher,AlbertVillanovadelMoral,ThomasWolf,LeandrovonWerra,andErikKaunismäki.smo-
lagents: A smol library to build great agentic systems. https://github.com/huggingface/smolagents,
| 2025. | Open-source | software. |     |     |     |     |     |
| ----- | ----------- | --------- | --- | --- | --- | --- | --- |
62

| Under review | as submission |     | to TMLR |     |     |     |     |     |     |     |     |
| ------------ | ------------- | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
Timo Schick, Jane Dwivedi-Yu, Roberto Dessì, Roberta Raileanu, Maria Lomeli, Eric Ham-
bro, Luke Zettlemoyer, Nicola Cancedda, and Thomas Scialom. Toolformer: Language mod-
| els can | teach themselves |     |     | to use tools. |          |     |     |                    |            |     | Systems, |
| ------- | ---------------- | --- | --- | ------------- | -------- | --- | --- | ------------------ | ---------- | --- | -------- |
|         |                  |     |     |               | Advances |     | in  | Neural Information | Processing |     |          |
36:68539–68551, 2023. URL https://proceedings.neurips.cc/paper_files/paper/2023/hash/
d842425e4bf79ba039352da0f658a906-Abstract-Conference.html.
Yonadav Shavit, Sandhini Agarwal, Miles Brundage, Steven Adler, Cullen O’Keefe, Rosie Campbell, Teddy
Lee, Pamela Mishkin, Tyna Eloundou, Alan Hickey, Katarina Slama, Lama Ahmad, Paul McMillan, An-
drea Vallone, Alexandre Passos, and David G. Robinson. Practices for governing agentic AI systems.
https://openai.com/index/practices-for-governing-agentic-ai-systems/, 2023. OpenAI publi-
cation.
Shivanshu Shekhar, Tanishq Dubey, Koyel Mukherjee, Apoorv Saxena, Atharv Tyagi, and Nishanth Kotla.
Towards optimizing the costs of llm usage. arXiv preprint arXiv:2402.01742, 2024.
Yongliang Shen, Kaitao Song, Xu Tan, Wenqi Zhang, Kan Ren, Siyu Yuan, Weiming Lu, Dong-
sheng Li, and Yueting Zhuang. TaskBench: Benchmarking large language models for task
| automation. |          |     |     |        |             |            |     | Systems, | 37:4540–4574, | 2024. | doi: |
| ----------- | -------- | --- | --- | ------ | ----------- | ---------- | --- | -------- | ------------- | ----- | ---- |
|             | Advances |     | in  | Neural | Information | Processing |     |          |               |       |      |
10.52202/079017-0148. URL https://proceedings.neurips.cc/paper_files/paper/2024/hash/
085185ea97db31ae6dcac7497616fd3e-Abstract-Datasets_and_Benchmarks_Track.html.
Tianneng Shi, Jingxuan He, Zhun Wang, Hongwei Li, Linyu Wu, Wenbo Guo, and Dawn Song. Progent:
Programmable privilege control for llm agents. arXiv preprint arXiv:2504.11703, 2025a.
Zhengliang Shi, Yuhan Wang, Lingyong Yan, Pengjie Ren, Shuaiqiang Wang, Dawei Yin, and Zhaochun
Ren. Retrieval models aren’t tool-savvy: Benchmarking tool retrieval for large language models. In
|          |                    |     |     |               |              |     |     | 2025, pp. 24497–24524, |     | Vienna, | Austria, |
| -------- | ------------------ | --- | --- | ------------- | ------------ | --- | --- | ---------------------- | --- | ------- | -------- |
| Findings | of the Association |     | for | Computational | Linguistics: |     | ACL |                        |     |         |          |
2025b. Association for Computational Linguistics. doi: 10.18653/v1/2025.findings-acl.1258. URL https:
//aclanthology.org/2025.findings-acl.1258/.
Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao.
| Reflexion: | Language | agents | with | verbal | reinforcement |     | learning. | In       |           |             |      |
| ---------- | -------- | ------ | ---- | ------ | ------------- | --- | --------- | -------- | --------- | ----------- | ---- |
|            |          |        |      |        |               |     |           | Advances | in Neural | Information | Pro- |
cessing Systems, volume 36, 2023. URL https://arxiv.org/abs/2303.11366.
Significant Gravitas. AutoGPT: Build, deploy, and run AI agents. GitHub repository, 2023. URL https:
//github.com/Significant-Gravitas/AutoGPT.
Skyvern-AI. Skyvern: Automate browser-based workflows with AI. GitHub repository, 2025. URL https:
//github.com/Skyvern-AI/skyvern.
Xiaoshuai Song, Haofei Chang, Guanting Dong, Yutao Zhu, Ji-Rong Wen, and Zhicheng Dou. Envs-
caler: Scaling tool-interactive environments for llm agent via programmatic synthesis. arXiv preprint
| arXiv:2601.05808, |     | 2026. |     |     |     |     |     |     |     |     |     |
| ----------------- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Tobin South, Samuele Marro, Thomas Hardjono, Robert Mahari, Cedric Deslandes Whitney, Alan Chan,
and Alex Pentland. Position: Ai agents need authenticated delegation. In
|            |            |     |          |          |       |        |       |     | Forty-second | International |     |
| ---------- | ---------- | --- | -------- | -------- | ----- | ------ | ----- | --- | ------------ | ------------- | --- |
| Conference | on Machine |     | Learning | Position | Paper | Track, | 2025. |     |              |               |     |
Joseph Spracklen, Raveen Wijewickrama, AHM Nazmus Sakib, Anindya Maiti, and Bimal Viswanath. We
have a package for you! a comprehensive analysis of package hallucinations by code generating {LLMs}.
In 34th USENIX Security Symposium (USENIX Security 25), pp. 3687–3706, 2025.
Shuang Sun, Huatong Song, Lisheng Huang, Jinhao Jiang, Ran Le, Zhihao Lv, Zongchao Chen, Yiwen Hu,
Wenyang Luo, Wayne Xin Zhao, Yang Song, Hongteng Xu, Tao Zhang, and Ji-Rong Wen. SWE-World:
Buildingsoftwareengineeringagents indocker-freeenvironments. arXiv:2602.03419, 2026.
|     |     |     |     |     |     |     |     | arXiv preprint |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | -------------- | --- | --- | --- |
Rao Surapaneni, Miku Jha, Michael Vakoc, and Todd Segal. Announcing the Agent2Agent proto-
col (A2A). Google Developers Blog, April 2025. URL https://developers.googleblog.com/en/
a2a-a-new-era-of-agent-interoperability/.
63

| Under review | as submission | to  | TMLR |     |     |     |     |     |
| ------------ | ------------- | --- | ---- | --- | --- | --- | --- | --- |
SWE-agent. Swe-agent. https://github.com/swe-agent/swe-agent, 2025. GitHub repository.
SWE-agentTeam. SWE-ReX:SWE-agentremoteexecutionframework. https://github.com/SWE-agent/
| swe-rex, | 2024. Open-source |     | software. |     |     |     |     |     |
| -------- | ----------------- | --- | --------- | --- | --- | --- | --- | --- |
Georgios Syros, Anshuman Suri, Jacob Ginesin, Cristina Nita-Rotaru, and Alina Oprea. Saga: A security
architecture for governing ai agentic systems. arXiv preprint arXiv:2504.21034, 2025.
Haoran Tan, Zeyu Zhang, Chen Ma, Xu Chen, Quanyu Dai, and Zhenhua Dong. Membench: Towards
more comprehensive evaluation on the memory of llm-based agents. In Findings of the Association for
|               |              |     | 2025, pp. | 19336–19352, | 2025. |     |     |     |
| ------------- | ------------ | --- | --------- | ------------ | ----- | --- | --- | --- |
| Computational | Linguistics: |     | ACL       |              |       |     |     |     |
TensorZero. TensorZero: An open-source stack for industrial-grade LLM applications. https://github.
| com/tensorzero/tensorzero, |               |                                               | 2026. |     |     |     |     |     |
| -------------------------- | ------------- | --------------------------------------------- | ----- | --- | --- | --- | --- | --- |
| Th0rgal.                   | sandboxed.sh: | Self-hostedorchestratorforAIautonomousagents. |       |     |     |     |     |     |
https://github.com/Th0rgal/
| sandboxed.sh, | 2026.       | Open-source                             | software. |     |     |     |     |     |
| ------------- | ----------- | --------------------------------------- | --------- | --- | --- | --- | --- | --- |
| thedotmack.   | claude-mem: | Plugin-stylememorylayerforcodingagents. |           |     |     |     |     |     |
https://github.com/thedotmack/
| claude-mem, | 2025. GitHub |     | repository. |     |     |     |     |     |
| ----------- | ------------ | --- | ----------- | --- | --- | --- | --- | --- |
Traceloop.OpenLLMetry: Open-sourceobservabilityforLLMapplicationsbasedonOpenTelemetry.https:
| //github.com/traceloop/openllmetry, |     |     | 2026. |     |     |     |     |     |
| ----------------------------------- | --- | --- | ----- | --- | --- | --- | --- | --- |
Trail of Bits. Jumping the line: How MCP servers can attack you before you ever use
| them. | Trail of | Bits Blog, | April 2025. | URL |     |     |     |     |
| ----- | -------- | ---------- | ----------- | --- | --- | --- | --- | --- |
https://blog.trailofbits.com/2025/04/21/
jumping-the-line-how-mcp-servers-can-attack-you-before-you-ever-use-them/.
Vivek Trivedy. Improving Deep Agents with harness engineering. https://www.langchain.com/blog/
| improving-deep-agents-with-harness-engineering, |     |     |     |     | 2026. | Blog post. |     |     |
| ----------------------------------------------- | --- | --- | --- | --- | ----- | ---------- | --- | --- |
Lillian Tsai and Eugene Bagdasarian. Contextual agent security: A policy for every purpose. In Proceedings
|        |               |        |                     | Systems, | pp. | 8–17, 2025. |     |     |
| ------ | ------------- | ------ | ------------------- | -------- | --- | ----------- | --- | --- |
| of the | 2025 Workshop | on Hot | Topics in Operating |          |     |             |     |     |
Shubham Ugare and Satish Chandra. Agentic code reasoning. arXiv preprint arXiv:2603.01896, 2026. URL
https://arxiv.org/abs/2603.01896.
AshishVaswani,NoamShazeer,NikiParmar,JakobUszkoreit,LlionJones,AidanNGomez,ŁukaszKaiser,
and Illia Polosukhin. Attention is all you need. Advances in neural information processing systems, 30,
2017.
Vectorize.io. Hindsight: Agentmemorythatlearns. https://github.com/vectorize-io/hindsight,2025.
| GitHub | repository. |     |     |     |     |     |     |     |
| ------ | ----------- | --- | --- | --- | --- | --- | --- | --- |
Vaishali Vinay. Failure modes in llm systems: A system-level taxonomy for reliable ai applications.
arXiv
| preprint | arXiv:2511.19933, |     | 2025. |     |     |     |     |     |
| -------- | ----------------- | --- | ----- | --- | --- | --- | --- | --- |
Eric Wallace, Kai Xiao, Reimar Leike, Lilian Weng, Johannes Heidecke, and Alex Beutel. The instruction
hierarchy: Training llms to prioritize privileged instructions. arXiv preprint arXiv:2404.13208, 2024.
Haoyu Wang, Christopher M Poskitt, and Jun Sun. Agentspec: Customizable runtime enforcement for safe
| and reliable | llm agents.(2026). |            | In          |        |          |               |            |             |
| ------------ | ------------------ | ---------- | ----------- | ------ | -------- | ------------- | ---------- | ----------- |
|              |                    |            | Proceedings | of the | IEEE/ACM | International | Conference | on Software |
| Engineering, | ICSE,              | pp. 12–18, | 2026.       |        |          |               |            |             |
Junlin Wang, Jue Wang, Ben Athiwaratkun, Ce Zhang, and James Zou. Mixture-of-agents enhances large
language model capabilities. arXiv preprint arXiv:2406.04692, 2024. URL https://arxiv.org/abs/
2406.04692.
64

| Under review | as submission |     | to  | TMLR |     |     |     |     |     |     |     |
| ------------ | ------------- | --- | --- | ---- | --- | --- | --- | --- | --- | --- | --- |
Xingyao Wang, Boxuan Li, Yufan Song, Frank F. Xu, Xiangru Tang, Mingchen Zhuge, Jiayi Pan, Yueqi
Song, Bowen Li, Jaskirat Singh, Hoang H. Tran, Fuqiang Li, Ren Ma, Mingzhang Zheng, Bill Qian,
Yanjun Shao, Niklas Muennighoff, Yizhe Zhang, Binyuan Hui, Junyang Lin, Robert Brennan, Hao Peng,
Heng Ji, and Graham Neubig. Openhands: An open platform for AI software developers as generalist
agents. In The Thirteenth International Conference on Learning Representations, 2025a. URL https:
//openreview.net/forum?id=OJd3ayDDoF.
XingyaoWang,BoxuanLi,YufanSong,FrankFXu,XiangruTang,MingchenZhuge,JiayiPan,YueqiSong,
Bowen Li, Jaskirat Singh, et al. Openhands: An open platform for ai software developers as generalist
agents. In International Conference on Learning Representations, volume 2025, pp. 65882–65919, 2025b.
Xingyao Wang, Simon Rosenberg, Juan Michelini, Calvin Smith, Hoang Tran, Engel Nyst, Rohit Malhotra,
Xuhui Zhou, Valerie Chen, Robert Brennan, et al. The openhands software agent sdk: A composable and
extensible foundation for production agents. arXiv preprint arXiv:2511.03690, 2025c.
Bowen Wei, Yunbei Zhang, Jinhao Pan, Kai Mei, Xiao Wang, Jihun Hamm, Ziwei Zhu, and Yingqiang Ge.
Clawsafety:" safe" llms, unsafe agents. arXiv preprint arXiv:2604.01438, 2026.
Yuhao Wu, Franziska Roesner, Tadayoshi Kohno, Ning Zhang, and Umar Iqbal. IsolateGPT:
An execution isolation architecture for LLM-based agentic systems. In Network and Distributed
System Security Symposium (NDSS), 2025. URL https://www.ndss-symposium.org/ndss-paper/
isolategpt-an-execution-isolation-architecture-for-llm-based-agentic-systems/.
Xi Xiao, Yunbei Zhang, Xingjian Li, Tianyang Wang, Xiao Wang, Yuxiang Wei, Jihun Hamm, and Min
| Xu. Visual  | instance-aware |            | prompt | tuning. | In  |             |     |              |               |            |     |
| ----------- | -------------- | ---------- | ------ | ------- | --- | ----------- | --- | ------------ | ------------- | ---------- | --- |
|             |                |            |        |         |     | Proceedings | of  | the 33rd ACM | International | Conference | on  |
| Multimedia, | pp.            | 2880–2889, |        | 2025.   |     |             |     |              |               |            |     |
TianbaoXie,DanyangZhang,JixuanChen,XiaochuanLi,SihengZhao,RuishengCao,TohJHua,Zhoujun
Cheng, Dongchan Shin, Fangyu Lei, et al. Osworld: Benchmarking multimodal agents for open-ended
tasks in real computer environments. Advances in Neural Information Processing Systems, 37:52040–
| 52094, 2024. |     |     |     |     |     |     |     |     |     |     |     |
| ------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Frank F Xu, Yufan Song, Boxuan Li, Yuxuan Tang, Kritanjali Jain, Mengxue Bao, Zora Z Wang, Xuhui
Zhou, Zhitong Guo, Murong Cao, et al. Theagentcompany: benchmarking llm agents on consequential
| real world | tasks. | arXiv | preprint | arXiv:2412.14161, |     | 2024. |     |     |     |     |     |
| ---------- | ------ | ----- | -------- | ----------------- | --- | ----- | --- | --- | --- | --- | --- |
Wujiang Xu, Zujie Liang, Kai Mei, Hang Gao, Juntao Tan, and Yongfeng Zhang. A-mem: Agentic memory
| for llm | agents. |     |          | arXiv:2502.12110, |     | 2025. |     |     |     |     |     |
| ------- | ------- | --- | -------- | ----------------- | --- | ----- | --- | --- | --- | --- | --- |
|         | arXiv   |     | preprint |                   |     |       |     |     |     |     |     |
Boyang Yan. Fault-tolerant sandboxing for ai coding agents: A transactional approach to safe autonomous
| execution. |     |     | arXiv:2512.12806, |     | 2025. |     |     |     |     |     |     |
| ---------- | --- | --- | ----------------- | --- | ----- | --- | --- | --- | --- | --- | --- |
arXiv preprint
John Yang, Carlos E Jimenez, Alexander Wettig, Kilian Lieret, Shunyu Yao, Karthik Narasimhan, and Ofir
Press. Swe-agent: Agent-computer interfaces enable automated software engineering.
|             |            |     |          |                 |     |       |     |     | Advances | in  | Neural |
| ----------- | ---------- | --- | -------- | --------------- | --- | ----- | --- | --- | -------- | --- | ------ |
| Information | Processing |     | Systems, | 37:50528–50652, |     | 2024. |     |     |          |     |        |
Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik R. Narasimhan, and Yuan Cao.
| ReAct: | Synergizing | reasoning |     | and acting | in language |     | models. | In           |               |            |     |
| ------ | ----------- | --------- | --- | ---------- | ----------- | --- | ------- | ------------ | ------------- | ---------- | --- |
|        |             |           |     |            |             |     |         | The Eleventh | International | Conference |     |
on Learning Representations, 2023. URL https://openreview.net/forum?id=WE_vluYUL-X.
Yuzhe Yu. Claude code reverse engineering: A tool to visualize Claude Code’s LLM interactions.
https:
| //github.com/Yuyz0112/claude-code-reverse, |     |     |     |     |     | 2026. |     |     |     |     |     |
| ------------------------------------------ | --- | --- | --- | --- | --- | ----- | --- | --- | --- | --- | --- |
Lifan Yuan, Yangyi Chen, Xingyao Wang, Yi R. Fung, Hao Peng, and Heng Ji. CRAFT: Customizing
LLMs by creating and retrieving from specialized toolsets. arXiv preprint arXiv:2309.17428, 2023. URL
https://arxiv.org/abs/2309.17428.
65

Under review as submission to TMLR
Siyu Yuan, Kaitao Song, Jiangjie Chen, Xu Tan, Yongliang Shen, Kan Ren, Dongsheng Li, and De-
qing Yang. EASYTOOL: Enhancing LLM-based agents with concise tool instruction. In Proceedings
of the 2025 Conference of the Nations of the Americas Chapter of the Association for Computational
Linguistics: Human Language Technologies (Volume 1: Long Papers), pp. 951–972, Albuquerque, New
Mexico, 2025. Association for Computational Linguistics. doi: 10.18653/v1/2025.naacl-long.44. URL
https://aclanthology.org/2025.naacl-long.44/.
YunbeiZhang,YingqiangGe,WeijieXu,YuhuiXu,JihunHamm,andChandanKReddy. Visualexclusivity
attacks: Automaticmultimodalredteamingviaagenticplanning. arXivpreprintarXiv:2603.20198,2026a.
Yunbei Zhang, Kai Mei, Ming Liu, Janet Wang, Dimitris N Metaxas, Xiao Wang, Jihun Hamm, and
Yingqiang Ge. Agents in the wild: Safety, society, and the illusion of sociality on moltbook. arXiv
preprint arXiv:2602.13284, 2026b.
ZeyuZhang,QuanyuDai,XiaoheBo,ChenMa,RuiLi,XuChen,JiemingZhu,ZhenhuaDong,andJi-Rong
Wen. A survey on the memory mechanism of large language model-based agents. ACM Transactions on
Information Systems, 43(6):1–47, 2025.
Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin,
Zhuohan Li, Dacheng Li, Eric Xing, et al. Judging llm-as-a-judge with mt-bench and chatbot arena.
Advances in neural information processing systems, 36:46595–46623, 2023.
YanZhao Zheng, ZhenTao Zhang, Chao Ma, YuanQiang Yu, JiHuai Zhu, Yong Wu, Tianze Xu, Baohua
Dong, Hangcheng Zhu, Ruohui Huang, and Gang Yu. SkillRouter: Skill routing for LLM agents at scale.
arXiv preprint arXiv:2603.22455, 2026. URL https://arxiv.org/abs/2603.22455.
YushengZheng,YanpengHu,TongYu,andAndiQuinn. Agentsight: System-levelobservabilityforaiagents
using ebpf. In Proceedings of the 4th Workshop on Practical Adoption Challenges of ML for Systems, pp.
110–115, 2025.
Wanjun Zhong, Lianghong Guo, Qiqi Gao, He Ye, and Yanlin Wang. Memorybank: Enhancing large
languagemodelswithlong-termmemory. InProceedings of the AAAI conference on artificial intelligence,
volume 38, pp. 19724–19731, 2024.
Shuyan Zhou, Frank F Xu, Hao Zhu, Xuhui Zhou, Robert Lo, Abishek Sridhar, Xianyi Cheng, Tianyue
Ou, Yonatan Bisk, Daniel Fried, et al. Webarena: A realistic web environment for building autonomous
agents. In International Conference on Learning Representations, volume 2024, pp. 15585–15606, 2024.
Yuhang Zhou, Lizhu Zhang, Yifan Wu, Jiayi Liu, Xiangjun Fan, Zhuokai Zhao, and Hong Yan. Synthetic
sandbox for training machine learning engineering agents. arXiv preprint arXiv:2604.04872, 2026.
KunlunZhu, ZijiaLiu, BingxuanLi, MuxinTian, YingxuanYang, JiaxunZhang, PengruiHan, QipengXie,
Fuyang Cui, Weijia Zhang, et al. Where LLM agents fail and how they can learn from failures. arXiv
preprint arXiv:2509.25370, 2025. URL https://arxiv.org/abs/2509.25370. arXiv:2509.25370.
66

| Under review | as submission | to TMLR   |         |     |
| ------------ | ------------- | --------- | ------- | --- |
| A Appendix:  | Full          | Ecosystem | Mapping |     |
Table S1 gives the technical ecosystem mapping used by this survey. The catalog snapshot was verified
on 2026-05-08 with 171 public entries, 146 GitHub entries, 142 GitHub entries in project categories, and 0
brokenURLs. Forthepaperappendix,wekeeponlytechnicalartifactsandthesevenETCLOVGlayers: pure
readings, ecosystem maps, general list repositories, and tutorial- or handbook-only resources are omitted.
Former reference implementations are folded into their dominant ETCLOVG layer using the catalog tags
and summaries; tags and star snapshots are copied from the verified snapshot. Appendix B expands the six
focal implementations.
TableS1: CuratedtechnicalecosystemcatalogwithoneprimaryETCLOVGlayerperartifact.
Primary
| Artifact |     |     | Catalog tags | Stars |
| -------- | --- | --- | ------------ | ----- |
layer
Execution Substrates & Sandboxing 20entries;primarylayer: E–Execution&Sandboxing
| Daytona            |     |     | E sandbox,execution,infra            | 72.4k |
| ------------------ | --- | --- | ------------------------------------ | ----- |
| NanoClaw           |     |     | E containers,claude-sdk,scheduling   | 28.6k |
| cmux               |     |     | E macos,workspace,browser            | 16.3k |
| CUA                |     |     | E computer-use,sandbox,infra         | 15.7k |
| E2B                |     |     | E cloud-sandbox,execution,enterprise | 12.1k |
| BrowserHarness     |     |     | E browser,cdp,self-healing           | 11.0k |
| OpenSandbox        |     |     | E sandbox,security,runtime           | 10.5k |
| agent-infrasandbox |     |     | E all-in-one,browser,shell           | 4.5k  |
| Judge0             |     |     | E code-execution,sandbox,backend     | 4.2k  |
| AgentSandbox       |     |     | E kubernetes,sandbox,stateful        | 2.1k  |
| stakpak/agent      |     |     | E always-on,autonomous,ops           | 1.5k  |
| OSS-FuzzGen        |     |     | E fuzzing,security,execution         | 1.4k  |
| E2BDesktopSandbox  |     |     | E desktop,sandbox,computer-use       | 1.4k  |
| Tensorlake         |     |     | E microvm,sandbox,orchestration      | 911   |
| Arrakis            |     |     | E sandbox,microvm,snapshots          | 808   |
| AgentScopeRuntime  |     |     | E runtime,sandbox,deployment         | 766   |
| SWE-ReX            |     |     | E sandbox,execution,coding-agent     | 490   |
| sandboxed.sh       |     |     | E self-hosted,isolation,orchestrator | 416   |
| Capsule            |     |     | E wasm,sandbox,task-runtime          | 281   |
| terminal-bench-env |     |     | E terminal,benchmark-env,sandbox     | 80    |
Protocols, Tool Interfaces & Agent Contracts 12entries;primarylayer: T–ToolInterface&Protocol
| GitHubSpecKit                   |     |     | T spec-driven,workflows,tooling        | 92.9k |
| ------------------------------- | --- | --- | -------------------------------------- | ----- |
| MCPServers                      |     |     | T mcp,servers,implementations          | 85.1k |
| CLI-Anything                    |     |     | T cli,tool-use,automation              | 33.7k |
| AGENTS.md                       |     |     | T spec,agent-file,instructions         | 21.0k |
| ModelContextProtocol            |     |     | T mcp,protocol,interoperability        | 8.0k  |
| directories(rulesandMCPindexes) |     |     | T directories,mcp,rules                | 3.9k  |
| LangChainMCPAdapters            |     |     | T mcp,adapters,integration             | 3.5k  |
| MicrosoftMCPServers             |     |     | T mcp,enterprise,servers               | 3.1k  |
| ACPX                            |     |     | T acp,client,sessions                  | 2.6k  |
| MicrosoftLearnMCP               |     |     | T mcp,docs,grounding                   | 1.6k  |
| IBMMCP                          |     |     | T mcp,clients,tooling                  | 374   |
| AGENT.md                        |     |     | T standard,agent-file,interoperability | 77    |
Context & Working-State Engineering 9entries;primarylayer: C–Context&WorkingState
| claude-mem           |     |     | C memory,context,session      | 72.8k |
| -------------------- | --- | --- | ----------------------------- | ----- |
| SuperClaudeFramework |     |     | C config,personas,workflow    | 22.6k |
| planning-with-files  |     |     | C planning,skills,persistence | 20.5k |
AgentSkillsforContextEngineering C skills,context,production 15.5k
| CCPM    |     |     | C planning,github-issues,parallel-execution | 8.1k |
| ------- | --- | --- | ------------------------------------------- | ---- |
| Trellis |     |     | C specs,memory,workflow                     | 7.2k |
Continued on next page
67

| Under review | as submission | to TMLR |     |     |
| ------------ | ------------- | ------- | --- | --- |
TableS1: CuratedtechnicalecosystemcatalogwithoneprimaryETCLOVGlayerperartifact(continued).
Primary
| Artifact |     |     | Catalog tags | Stars |
| -------- | --- | --- | ------------ | ----- |
layer
| OSAURUS       |     |     | C macos,local-first,memory           | 5.2k |
| ------------- | --- | --- | ------------------------------------ | ---- |
| holaOS        |     |     | C long-horizon,desktop,durable-state | 4.9k |
| context-space |     |     | C context,infrastructure,mcp         | 809  |
Harness Architecture & Orchestration 47entries;primarylayer: L–Lifecycle&Orchestration
| OpenCode   |     |     | L terminal,coding-agent,subagents        | 155.8k |
| ---------- | --- | --- | ---------------------------------------- | ------ |
| ClaudeCode |     |     | L terminal,coding-agent,git-workflows    | 120.9k |
| GeminiCLI  |     |     | L terminal,coding-agent,mcp              | 103.3k |
| CodexCLI   |     |     | L terminal,coding-agent,local-execution  | 80.4k  |
| OpenHands  |     |     | L coding-agent,software-engineering,repo | 72.7k  |
| DeerFlow   |     |     | L long-horizon,memory,subagents          | 65.4k  |
| AutoGen    |     |     | L multi-agent,orchestration,framework    | 57.8k  |
| OpenManus  |     |     | L general-agent,autonomy,workflows       | 56.0k  |
| pi         |     |     | L coding-agent,runtime,monorepo          | 46.5k  |
| aider      |     |     | L terminal,repo-map,testing              | 44.4k  |
| Agno       |     |     | L scale,runtime,management               | 39.9k  |
ClaudeCodePlugins: Orchestrationand L claude-code,plugins,orchestration 34.9k
Automation
| LangGraph               |     |     | L graph,workflow,runtime               | 31.3k |
| ----------------------- | --- | --- | -------------------------------------- | ----- |
| SemanticKernel          |     |     | L enterprise,orchestration,plugins     | 27.8k |
| OpenAIAgentsSDK(Python) |     |     | L sdk,handoff,workflows                | 25.9k |
| QwenCode                |     |     | L terminal,coding-agent,cli            | 24.2k |
| deepagents              |     |     | L runtime,orchestration,long-running   | 22.3k |
| Archon                  |     |     | L workflow-engine,worktrees,validation | 20.9k |
| Devika                  |     |     | L assistant,planning,coding            | 19.5k |
| GoogleADK(Python)       |     |     | L toolkit,deployment,evaluation        | 19.5k |
| SWE-agent               |     |     | L swe,issue-fixing,tooling             | 19.1k |
| PydanticAI              |     |     | L python,typing,schema                 | 16.9k |
| Aperant                 |     |     | L coding-agent,parallel,memory         | 14.2k |
| Eigent                  |     |     | L desktop,cowork,productivity          | 13.9k |
| OpenHarness             |     |     | L tool-use,memory,multi-agent          | 12.0k |
| Superset                |     |     | L worktrees,desktop,parallel           | 10.4k |
| GitHubCopilotCLI        |     |     | L terminal,coding-agent,mcp            | 10.4k |
| Hive                    |     |     | L harness,orchestration,runtime        | 10.2k |
MicrosoftAgentFramework L multi-agent,workflows,observability 10.2k
| OpenSWE          |     |     | L async,coding-agent,swe                     | 9.7k |
| ---------------- | --- | --- | -------------------------------------------- | ---- |
| VoltAgent        |     |     | L typescript,platform,runtime                | 8.7k |
| mcp-agent        |     |     | L mcp,runtime,workflow                       | 8.3k |
| Yao              |     |     | L single-binary,runtime,autonomous           | 7.5k |
| Paseo            |     |     | L coding-agent,daemon,multi-device           | 5.5k |
| 1Code            |     |     | L coding-agent,orchestration,worktrees       | 5.5k |
| CloudflareAgents |     |     | L platform,deployment,runtime                | 4.9k |
| HiClaw           |     |     | L multi-agent,human-in-the-loop,shared-state | 4.4k |
| mini-swe-agent   |     |     | L minimal,swe,coding-agent                   | 4.2k |
| oh-my-pi         |     |     | L terminal,lsp,subagents                     | 4.0k |
| TinyAGI          |     |     | L team-orchestration,autonomous,workflows    | 3.6k |
| Devon            |     |     | L pair-programming,coding-agent,autonomous   | 3.4k |
| OpenClaudeCowork |     |     | L desktop,ui,orchestration                   | 3.3k |
| DockerAgent      |     |     | L docker,runtime,container                   | 2.9k |
| NeMoAgentToolkit |     |     | L multi-agent,optimization,toolkit           | 2.3k |
| Scion            |     |     | L multi-agent,containers,orchestration       | 1.4k |
| deepagentsjs     |     |     | L typescript,langgraph,subagents             | 1.2k |
Continued on next page
68

| Under review | as submission | to TMLR |     |     |
| ------------ | ------------- | ------- | --- | --- |
TableS1: CuratedtechnicalecosystemcatalogwithoneprimaryETCLOVGlayerperartifact(continued).
Primary
| Artifact |     |     | Catalog tags | Stars |
| -------- | --- | --- | ------------ | ----- |
layer
| hankweave |     |     | L long-horizon,runtime,checkpoints | 120 |
| --------- | --- | --- | ---------------------------------- | --- |
Observability & Reliability Operations 15entries;primarylayer: O–Observability&Operations
| Langfuse                      |     |     | O llmops,tracing,metrics                | 26.7k |
| ----------------------------- | --- | --- | --------------------------------------- | ----- |
| MLflow                        |     |     | O platform,monitoring,evaluation        | 25.8k |
| Opik                          |     |     | O monitoring,eval,tracing               | 19.2k |
| RagaAICatalyst                |     |     | O agentops,analytics,monitoring         | 16.2k |
| TensorZero                    |     |     | O llmops,gateway,optimization           | 11.3k |
| ArizePhoenix                  |     |     | O observability,tracing,evaluation      | 9.5k  |
| OpenLLMetry                   |     |     | O opentelemetry,instrumentation,tracing | 7.1k  |
| Helicone                      |     |     | O monitoring,traffic,production         | 5.6k  |
| AgentOpsSDK                   |     |     | O agentops,monitoring,cost              | 5.5k  |
| Latitude                      |     |     | O platform,eval,observability           | 4.0k  |
| Laminar                       |     |     | O observability,tracing,evals           | 2.8k  |
| AmazonBedrockAgentCoreSamples |     |     | O aws,runtime,operations                | 2.8k  |
| claude-code-reverse           |     |     | O trace,visualization,debugging         | 2.4k  |
| OpenInference                 |     |     | O spec,instrumentation,observability    | 953   |
| FutureAGI                     |     |     | O observability,evaluation,guardrails   | 843   |
Evaluation Harnesses & Benchmarks 21entries;primarylayer: V–Verification&Evaluation
| Promptfoo             |     |     | V eval,red-team,ci                   | 20.9k |
| --------------------- | --- | --- | ------------------------------------ | ----- |
| DeepEval              |     |     | V evaluation,framework,testing       | 15.2k |
| RAGAS                 |     |     | V rag,metrics,evaluation             | 13.8k |
| lm-evaluation-harness |     |     | V benchmark,harness,llm              | 12.4k |
| SWE-bench             |     |     | V benchmark,swe,evaluation           | 4.9k  |
| verifiers             |     |     | V verifier,rl,evaluation             | 4.1k  |
| AgentBench            |     |     | V benchmark,cross-domain,agent       | 3.4k  |
| LangWatch             |     |     | V simulation,evaluation,testing      | 3.2k  |
| EvalScope             |     |     | V benchmark,framework,llm            | 2.8k  |
| Terminal-Bench        |     |     | V terminal,benchmark,long-horizon    | 2.2k  |
| Harbor                |     |     | V evaluation,harness,rl-env          | 1.8k  |
| tau2-bench            |     |     | V tool-use,interaction,benchmark     | 1.1k  |
| NeMoGym               |     |     | V rl-env,training,evaluation         | 872   |
| TheAgentCompany       |     |     | V benchmark,workplace,multi-step     | 697   |
| auto-harness          |     |     | V optimization,regression,evals      | 486   |
| InspectEvals          |     |     | V inspect,eval-suite,reproducibility | 480   |
| SWE-BenchPro          |     |     | V swe,benchmark,long-horizon         | 371   |
| AgentEvaluation       |     |     | V evaluation,testing,ci              | 360   |
| WorkArena             |     |     | V browser,benchmark,enterprise       | 245   |
| OpenHandsBenchmarks   |     |     | V openhands,eval,harness             | 77    |
| WebArena-Verified     |     |     | V web-agent,benchmark,deterministic  | 38    |
Guardrails, Security & Governance 14entries;primarylayer: G–Governance&Security
| LiteLLM              |     |     | G gateway,proxy,guardrails         | 45.9k |
| -------------------- | --- | --- | ---------------------------------- | ----- |
| Kong                 |     |     | G gateway,policy,infra             | 43.3k |
| IronClaw             |     |     | G security,wasm,routines           | 12.1k |
| PortkeyGateway       |     |     | G gateway,guardrails,routing       | 11.6k |
| CAI(CybersecurityAI) |     |     | G security,governance,framework    | 8.4k  |
| OpenAIRealtimeAgents |     |     | G realtime,orchestration,control   | 6.8k  |
| Plano                |     |     | G proxy,safety,data-plane          | 6.4k  |
| OpenAICSAgentsDemo   |     |     | G demo,handoffs,governance         | 6.3k  |
| ContextForge         |     |     | G gateway,governance,observability | 3.7k  |
| Archestra            |     |     | G enterprise,guardrails,governance | 3.6k  |
| Tracecat             |     |     | G security,automation,policy       | 3.6k  |
Continued on next page
69

| Under review | as submission | to TMLR |     |     |
| ------------ | ------------- | ------- | --- | --- |
TableS1: CuratedtechnicalecosystemcatalogwithoneprimaryETCLOVGlayerperartifact(continued).
Primary
| Artifact |     |     | Catalog tags | Stars |
| -------- | --- | --- | ------------ | ----- |
layer
| AgentGateway      |     |     | G gateway,mcp,proxy              | 2.6k |
| ----------------- | --- | --- | -------------------------------- | ---- |
| Haft              |     |     | G governance,decisions,mcp       | 1.3k |
| mini-coding-agent |     |     | G coding-agent,minimal,approvals | 807  |
70

Under review as submission to TMLR
B Appendix: Reference Harness Implementations
Table S2 profiles the six reference implementations requested for closer comparison. The entries are
mechanism-focusedratherthanproduct-marketingsummaries: eachrowlistsonlyclaimsthataresupported
by the cited public repository, paper, documentation, or engineering writeup.
Table S2: Reference harness implementations and their documented ETCLOVG coverage.
Implementation and Harness pattern and layers Design signal for this survey
source
Claude Code Terminal coding agent; single-agent A production reference for high-autonomy local coding
(Anthropic,2025;a;b) edit,debug,andGitloop. workflows: codebase-awareprompting,shell/toolexecution,
Layers: E,T,C,L,G repositoryedits,andexplicitpermissionorsandboxbound-
ariesaretreatedasharnessresponsibilities.
OpenCode Open-source terminal coding agent Useful as an inspectable implementation of the modern
(Anomaly,2025) withplan/buildroles,subagents,LSP terminal-agent loop, especially where role separation, sub-
support,andclient-serverruntime. agentdelegation,andeditor/toolintegrationareexposedin
Layers: E,T,L therepository.
Codex CLI Terminal-native coding agent; state- OpenAI’s Codex writeups make the harness loop explicit:
(OpenAI,2025;2026b;a) lessreplay-orientedsingle-agentloop. structuredprompts,tool-callreplay,localcommandexecu-
Layers: E,T,L,V tion,andtestorverificationfeedbackjointlydeterminethe
agentbehavior.
OpenHands Opensoftware-engineeringagentplat- A research-grade reference for repo-level software
(Wangetal.,2025b;c) formandcomposableagentSDK. agents: the platform couples sandboxed execution,
Layers: E,T,C,L,V shell/browser/tool interaction, task state, and benchmark-
orientedevaluationinoneopensystem.
SWE-agent Issue-fixing coding agent centered Thekeycontributionistheagent-computerinterface: com-
(Yangetal.,2024;SWE- on an agent-computer interface and mands,observations,editingactions,tests,andremoteexe-
agent, 2025; SWE-agent SWE-ReXexecutionbackends. cutionbackendsbecomepartofthemeasuredharnessrather
Team,2024) Layers: E,T,L,V thanincidentalinfrastructure.
Symphony Codex orchestration spec and task- Symphony treats the issue tracker and task runner as a
(OpenAI, 2026b; runnerworkflowforissue-to-execution durable control plane, making assignment, progress state,
Kotliarskyietal.,2026) control. validation gates, and review boundaries explicit parts of
Layers: C,L,V,G Codexorchestration.
71