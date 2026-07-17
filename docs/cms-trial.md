# CMS TRIAL / CMS向けAI活用トライアル

## English Version

## 1. Overview

FPT proposes a **one-month free AI Proof of Concept (PoC)** for Osaka Gas Marketing.

The engagement will follow a **mini FDE-style approach**: FPT will work closely with business end users, observe actual operations, identify high-value AI opportunities, rapidly test ideas, and validate whether AI can improve real work rather than only demonstrate technical capability.

During the first two weeks, an FPT BA Lead will work onsite with Osaka Gas Marketing’s end users. The remaining two weeks will focus on implementing and evaluating one or two prioritized workflows.

## 2. PoC Objectives

The PoC aims to:

- Understand actual end-user workflows and operational pain points.
- Identify tasks suitable for AI assistance or partial automation.
- Validate data, security, usability, and technical feasibility.
- Measure potential time savings and quality improvement.
- Select practical use cases for a future paid pilot or production phase.

## 3. Proposed One-Month Approach

### Weeks 1–2: Onsite workflow discovery and rapid trial

The FPT BA Lead will sit with representative end users and perform the following activities:

1. Observe actual daily work, including the use of email, Excel, documents, and internal systems.
2. Map the current As-Is workflow, inputs, outputs, decision points, business rules, and exceptions.
3. Identify repetitive work, manual copy-and-paste, information searching, document creation, summarization, and other potential AI opportunities.
4. Collect representative cases, templates, and sample data permitted for PoC use.
5. Create rapid prompts, mock-ups, or lightweight prototypes.
6. Ask end users to test early outputs and provide immediate feedback.
7. Prioritize one or two workflows for the second half of the PoC.

The working cycle will be:

> Observe → Map → Identify → Prototype → User Feedback → Prioritize

### Detailed plan for the first two weeks

The following plan assumes ten business days of onsite activity. The exact sequence may be adjusted according to end-user availability and data-access conditions.

| Day | Main objective | FPT BA Lead activities | Customer/end-user participation | Expected output |
|---|---|---|---|---|
| Day 1 | Kickoff and operating-condition confirmation | Confirm objectives, scope, candidate departments, working method, data restrictions, AI-service restrictions, and escalation route | Business owner, PoC coordinator, IT/Security, and key users attend the kickoff and confirm restrictions | Agreed PoC scope, stakeholder list, access rules, interview and shadowing schedule |
| Day 2 | Understand target operations | Interview key users and collect a high-level inventory of recurring work, inputs, outputs, systems, handoffs, and pain points | Key users explain their responsibilities and representative daily/weekly tasks | Initial workflow inventory and candidate use-case list |
| Day 3 | Workflow shadowing A | Observe selected users performing actual work; capture steps, time, decisions, tools, rework, and exceptions | End users perform normal work and explain the reason behind each important action | Draft As-Is workflow A, pain points, rule and exception log |
| Day 4 | Workflow shadowing B | Observe a second workflow or user group and compare differences between standard practice and individual workarounds | End users provide normal, complex, and failed cases where permitted | Draft As-Is workflow B and representative case set |
| Day 5 | Week 1 synthesis and prioritization checkpoint | Consolidate findings, quantify pain points, score use cases by business value, feasibility, data readiness, and risk | Business owner and key users review findings and correct misunderstandings | Validated workflow maps and shortlist of two to four AI opportunities |
| Day 6 | AI opportunity design | Define the target AI-assisted workflow, human-review points, required input, expected output, and evaluation method | Key users confirm acceptable and unacceptable AI behavior | To-Be concept, AI task boundary, initial success criteria |
| Day 7 | Rapid trial preparation | Build prompts, mock-ups, or lightweight prototype flows using approved sample data; prepare test cases and evaluation sheets | End users provide missing examples, templates, and expected answers | Trial-ready prototype and test scenario set |
| Day 8 | End-user trial round 1 | Facilitate user testing, compare output with existing work, capture errors, missing rules, correction time, and usability issues | End users test representative cases and explain why outputs are correct, incomplete, or unacceptable | Trial results, issue list, missing-rule list, prototype improvement backlog |
| Day 9 | Prototype refinement and trial round 2 | Refine the prototype and rerun priority cases; estimate potential time savings and human-review effort | Key users retest improved outputs and confirm remaining gaps | Updated prototype, preliminary KPI results, risk and control points |
| Day 10 | Week 2 decision gate | Present findings, rank use cases, confirm feasibility and limitations, and propose the scope for Weeks 3–4 | Business owner, key users, and IT/Security select one or two workflows and confirm evaluation criteria | Approved use cases for Weeks 3–4, agreed KPI, decision log, implementation backlog |

### Week 1 checkpoint

By the end of Week 1, both parties should confirm:

- Which workflows were actually observed.
- Whether the documented As-Is workflow is accurate.
- Which pain points are material and measurable.
- Which data and documents may be used for rapid trials.
- Which two to four AI opportunities should proceed to validation.

### Week 2 decision gate

By the end of Week 2, both parties should confirm:

- One or two prioritized workflows for implementation in Weeks 3–4.
- The expected AI role: drafting, searching, summarizing, checking, recommendation, or partial automation.
- Mandatory human-review and approval points.
- KPI baseline and target values.
- Known security, data, integration, and operational constraints.
- Conditions for recommending a paid pilot or production phase.

### Weeks 3–4: Focused implementation and evaluation

FPT will:

- Improve the selected prototype or workflow.
- Test it with representative business cases.
- Compare the AI-assisted process with the current process.
- Measure time reduction, output quality, accuracy, and required human correction.
- Identify risks, limitations, and mandatory human-review points.
- Prepare the final recommendation and next-step proposal.

## 4. Customer Actions and Confirmations Required

### 4.1 Data and AI usage policy

Before onsite activities begin, Osaka Gas Marketing should confirm:

- Which data and documents FPT may view during the PoC.
- Whether data may leave the customer environment.
- Whether cloud AI services or external LLM APIs may be used.
- Which information must be masked, anonymized, or replaced with test data.
- Whether prompts and outputs may be stored for evaluation.
- Requirements related to model-provider data retention or model training.
- Any prohibited data categories, systems, screens, or documents.

### 4.2 End-user nomination and workflow shadowing

Osaka Gas Marketing should nominate approximately **three to five representative end users** covering the main target operations.

The BA Lead should be allowed to observe how end users actually perform work, including:

- Where requests and input data originate.
- How users check and interpret information.
- Which rules or personal experience influence decisions.
- Which systems, files, and communication channels are used.
- Where delays, rework, or errors frequently occur.
- How normal and exceptional cases are handled.

### 4.3 Representative cases and materials

For each candidate workflow, end users should provide representative materials where permitted, such as:

- Five to ten sample cases.
- Matching input and final output examples.
- Excel templates, reports, emails, proposals, manuals, and FAQs.
- Examples of normal, complex, and previously failed cases.
- Business rules, review criteria, and common exceptions.

When real data cannot be shared, the customer should provide masked, anonymized, synthetic, or test data that remains representative of the actual workflow.

### 4.4 End-user participation in rapid trials

End users should participate in short validation cycles during the onsite period.

They will be expected to:

- Review the As-Is workflow documented by FPT.
- Test prompts, mock-ups, or prototype outputs using representative cases.
- Explain specifically why an output is correct, incorrect, or incomplete.
- Identify missing business rules and unacceptable risks.
- Confirm which steps AI may support and which steps require human judgment.
- Compare the AI-assisted process with the current way of working.

### 4.5 Business ownership and timely decisions

Osaka Gas Marketing should assign a business owner who can:

- Confirm workflow priorities.
- Resolve scope questions.
- Coordinate end users and internal stakeholders.
- Review findings at the end of each week.
- Select one or two use cases at the end of Week 2.
- Participate in the final go/no-go and next-step evaluation.

## 5. Expected Customer Resources

| Role | Expected participation |
|---|---|
| Business owner | Approximately 1 hour per week for review and decisions |
| Each key user | Approximately 3–5 hours during the first two weeks for observation, interviews, testing, and review |
| IT/Security representative | One or two sessions to confirm data, AI, environment, access, and security conditions |
| PoC coordinator | Coordinate schedules, workspace, accounts, materials, and stakeholder communication |

For onsite work, Osaka Gas Marketing may also need to provide:

- Workspace and site access for the FPT BA Lead.
- Network and device arrangements compliant with customer policy.
- Temporary accounts or supervised access where required.
- Approval for workflow observation and note-taking.

## 6. Expected Outputs After the First Two Weeks

FPT and Osaka Gas Marketing should jointly confirm:

1. List of workflows investigated.
2. As-Is workflow maps.
3. Pain points, current processing time, and major sources of rework.
4. Candidate AI opportunities.
5. Data readiness, security constraints, and feasibility assessment.
6. Results of initial rapid trials.
7. One or two prioritized workflows for Weeks 3–4.
8. Agreed success criteria and evaluation method.

## 7. Example Success Criteria

Depending on the selected workflow, success may be assessed using:

- Reduction in processing time per case.
- Reduction in manual steps or copy-and-paste work.
- Percentage of AI output accepted without major correction.
- Accuracy and completeness against business rules.
- Number and severity of errors or omissions.
- End-user usability and willingness to adopt.
- Clear identification of mandatory human-review points.

## 8. Final PoC Evaluation

At the end of the month, both parties will evaluate:

- Which workflows demonstrated measurable business value.
- Which workflows require more data, integration, or policy clarification.
- Whether AI should assist users or automate selected steps.
- Risks and controls required for broader adoption.
- Recommended scope for a paid pilot or production implementation.

## 9. Key Assumption

Although FPT will provide the one-month PoC without charge, successful validation requires active customer participation.

FPT will provide AI and engineering expertise, onsite business analysis, workflow design, and rapid prototyping. Osaka Gas Marketing will provide domain knowledge, representative data or test cases, end-user participation, timely feedback, and necessary approvals.

Without sufficient access to actual workflows, representative cases, and user feedback, the PoC may demonstrate only technical feasibility and may not be able to validate operational business value.

---

# 日本語版

## 1. 概要

FPTは、大阪ガスマーケティング様に対し、**1か月間の無償AI PoC（概念実証）**を提案します。

本PoCでは、一般的なAIデモではなく、現場業務に密着した**ミニFDE型の伴走アプローチ**を採用します。FPTが業務ユーザーと直接連携し、実際の業務を観察した上で、業務効果の高いAI活用機会を特定し、短いサイクルで試作・検証を行います。

最初の2週間は、FPTのBA Leadが大阪ガスマーケティング様の拠点に常駐し、業務ユーザーとともに業務分析および簡易トライアルを実施します。後半2週間は、優先順位の高い1～2件の業務フローを対象に、プロトタイプの改善と効果検証を行います。

## 2. PoCの目的

本PoCの目的は以下のとおりです。

- 業務ユーザーが実際に行っている業務フローと課題を把握する。
- AIによる支援または部分自動化に適した業務を特定する。
- データ利用、セキュリティ、ユーザビリティおよび技術的実現性を確認する。
- 作業時間の削減および成果物品質の改善可能性を測定する。
- 有償パイロットまたは本番導入に進める実用的なユースケースを選定する。

## 3. 1か月間の実施方針

### 第1～2週：現地での業務把握および簡易トライアル

FPTのBA Leadは、代表業務を担当する業務ユーザーの近くで、以下の活動を実施します。

1. メール、Excel、各種文書、社内システムなどを用いた日常業務を観察する。
2. 現行業務のAs-Isフロー、インプット、アウトプット、判断ポイント、業務ルールおよび例外ケースを整理する。
3. 繰り返し作業、転記、コピー＆ペースト、情報検索、資料作成、要約など、AI活用候補を特定する。
4. PoCで利用可能な代表ケース、テンプレートおよびサンプルデータを収集する。
5. プロンプト、モックアップまたは簡易プロトタイプを短期間で作成する。
6. 業務ユーザーに初期結果を確認いただき、即時フィードバックを得る。
7. 後半2週間で検証する1～2件の業務フローを選定する。

基本的な検証サイクルは以下のとおりです。

> Observe（観察）→ Map（可視化）→ Identify（候補特定）→ Prototype（試作）→ User Feedback（評価）→ Prioritize（優先順位決定）

### 最初の2週間の詳細計画

以下は、10営業日の現地活動を想定した標準計画です。実際の日程は、業務ユーザーの予定およびデータ利用条件に応じて調整します。

| 日程 | 主な目的 | FPT BA Leadの活動 | お客様・業務ユーザーにお願いする事項 | 主な成果物 |
|---|---|---|---|---|
| 1日目 | キックオフおよび実施条件の確認 | 目的、対象範囲、候補部門、進め方、データ制約、利用可能なAIサービス、課題エスカレーション先を確認 | Business Owner、PoC Coordinator、IT／Security担当およびKey Userにご参加いただき、制約事項を確認 | PoC対象範囲、関係者一覧、アクセスルール、ヒアリング・業務観察スケジュール |
| 2日目 | 対象業務の全体把握 | Key Userへのヒアリングを行い、定常業務、インプット、アウトプット、利用システム、部門間連携および課題を一覧化 | 担当業務、日次・週次作業および代表的な課題を説明 | 業務一覧および初期ユースケース候補 |
| 3日目 | 業務観察A | 対象ユーザーの実作業を観察し、作業手順、所要時間、判断、利用ツール、手戻りおよび例外を記録 | 通常業務を実施し、重要な操作や判断の理由を説明 | As-Is業務フローA、課題一覧、業務ルール・例外一覧 |
| 4日目 | 業務観察B | 別業務または別ユーザーグループを観察し、標準手順と個人対応の差異を整理 | 許可された範囲で通常ケース、複雑ケース、過去の失敗ケースを提供 | As-Is業務フローB、代表ケースセット |
| 5日目 | 第1週の整理および優先順位確認 | 調査結果を統合し、Business Value、実現性、データ準備状況、リスクの観点で候補を評価 | Business OwnerおよびKey Userに内容をレビューいただき、認識誤りを修正 | 確認済み業務フローおよび2～4件のAI活用候補 |
| 6日目 | AI活用方式の設計 | AI支援後の業務フロー、Human Reviewポイント、必要な入力、期待出力および評価方法を定義 | AIが実施してよいこと、実施してはいけないことを確認 | To-Beコンセプト、AI適用範囲、初期評価指標 |
| 7日目 | 簡易トライアル準備 | 承認済みサンプルデータを用いて、プロンプト、モックアップまたは簡易プロトタイプを作成し、評価シートを準備 | 不足しているケース、テンプレートおよび期待結果を提供 | トライアル可能なプロトタイプおよびテストシナリオ |
| 8日目 | ユーザートライアル1回目 | ユーザーテストを支援し、現行業務との比較、誤り、不足ルール、修正時間および操作性を記録 | 代表ケースでテストし、結果が正しい、足りない、または許容できない理由を説明 | トライアル結果、課題一覧、不足ルール一覧、改善バックログ |
| 9日目 | 改善およびユーザートライアル2回目 | プロトタイプを改善して優先ケースを再実行し、時間削減効果とHuman Review負荷を試算 | 改善版を再評価し、残課題を確認 | 改善版プロトタイプ、暫定KPI、リスクおよび統制ポイント |
| 10日目 | 第2週のDecision Gate | 調査・検証結果、優先順位、実現性、制約および後半2週間の提案範囲を説明 | Business Owner、Key UserおよびIT／Security担当により、対象1～2件と評価基準を決定 | 第3～4週の対象ユースケース、KPI、決定事項一覧、実装バックログ |

### 第1週終了時の確認事項

第1週終了時に、両社で以下を確認します。

- 実際に観察した業務フロー。
- 作成したAs-Is業務フローの正確性。
- 重要かつ測定可能な業務課題。
- 簡易トライアルで利用可能なデータおよび文書。
- 第2週で検証を進める2～4件のAI活用候補。

### 第2週終了時のDecision Gate

第2週終了時に、両社で以下を合意します。

- 第3～4週で実装・評価する1～2件の優先業務フロー。
- AIの役割：ドラフト作成、情報検索、要約、チェック、提案、または部分自動化。
- 必須となるHuman Reviewおよび承認ポイント。
- 現状値と目標値を含むKPI。
- データ、セキュリティ、システム連携および運用上の制約。
- 有償パイロットまたは本番導入を提案するための条件。

### 第3～4週：重点実装および効果検証

FPTは以下を実施します。

- 選定されたプロトタイプまたは業務フローを改善する。
- 代表的な業務ケースを用いて検証する。
- AI支援後の業務と現行業務を比較する。
- 作業時間削減、成果物品質、正確性および人手修正量を測定する。
- リスク、制約および必須のHuman Reviewポイントを整理する。
- 最終評価および次フェーズの提案を作成する。

## 4. お客様に実施・確認いただきたい事項

### 4.1 データおよびAI利用方針の確認

現地活動の開始前に、以下をご確認いただきます。

- FPTがPoC中に閲覧可能なデータおよび文書。
- データをお客様環境外へ持ち出すことの可否。
- クラウドAIサービスまたは外部LLM APIの利用可否。
- マスキング、匿名化またはテストデータへの置換が必要な情報。
- 評価目的でのプロンプトおよび出力結果の保存可否。
- AIサービス提供事業者によるデータ保持またはモデル学習に関する要件。
- 利用禁止となるデータ分類、システム画面または文書。

### 4.2 業務ユーザーの選定および業務観察

主要対象業務をカバーする**3～5名程度の代表業務ユーザー**を選定いただきます。

FPT BA Leadが以下を確認できるよう、実業務の観察機会をご提供いただきます。

- 依頼および入力データの発生元。
- ユーザーが情報を確認・解釈する方法。
- 判断に影響する業務ルールまたは個人経験。
- 利用するシステム、ファイルおよびコミュニケーション手段。
- 遅延、手戻りまたはミスが発生しやすい箇所。
- 通常ケースおよび例外ケースの対応方法。

### 4.3 代表ケースおよび資料の提供

各候補業務について、許可された範囲で以下をご提供いただきます。

- 5～10件のサンプルケース。
- 対応する入力データと最終成果物。
- Excelテンプレート、レポート、メール、提案書、マニュアルおよびFAQ。
- 通常ケース、複雑ケースおよび過去に問題が発生したケース。
- 業務ルール、レビュー基準および主な例外条件。

実データを共有できない場合は、実際の業務特性を維持したマスキング済みデータ、匿名化データ、合成データまたはテストデータをご準備いただきます。

### 4.4 簡易トライアルへの業務ユーザー参加

現地活動中は、業務ユーザーに短い検証サイクルへ参加いただきます。

主な実施事項は以下のとおりです。

- FPTが作成したAs-Is業務フローのレビュー。
- 代表ケースを用いたプロンプト、モックアップまたはプロトタイプのテスト。
- 出力が正しい、誤っている、または不足している理由の具体的な説明。
- 不足している業務ルールおよび許容できないリスクの指摘。
- AIが支援可能な工程と、人の判断が必要な工程の確認。
- AI支援後の業務と現行業務の比較。

### 4.5 Business Ownerの選任および迅速な意思決定

大阪ガスマーケティング様には、以下を実施できるBusiness Ownerを選任いただきます。

- 業務フローの優先順位確認。
- 対象範囲に関する課題の解決。
- 業務ユーザーおよび関係部門の調整。
- 各週末の調査・検証結果レビュー。
- 第2週終了時における1～2件のユースケース選定。
- 最終的なGo／No-Goおよび次フェーズ評価への参加。

## 5. 想定するお客様側リソース

| 役割 | 想定する参加内容 |
|---|---|
| Business Owner | 週約1時間のレビューおよび意思決定 |
| 各Key User | 最初の2週間に合計約3～5時間の業務観察、ヒアリング、テストおよびレビュー |
| IT／Security担当 | データ、AI、環境、アクセスおよびセキュリティ条件を確認する1～2回の打合せ |
| PoC Coordinator | 日程、作業場所、アカウント、資料および関係者間の調整 |

現地活動にあたり、必要に応じて以下のご準備をお願いします。

- FPT BA Leadの作業スペースおよび入館手続き。
- お客様ポリシーに準拠したネットワークおよび端末。
- 必要な一時アカウントまたは監督付きアクセス。
- 業務観察およびメモ作成に関する承認。

## 6. 最初の2週間終了時の想定成果物

FPTと大阪ガスマーケティング様で以下を共同確認します。

1. 調査対象となった業務フロー一覧。
2. As-Is業務フロー図。
3. 業務課題、現在の処理時間および主な手戻り要因。
4. AI活用候補一覧。
5. データ準備状況、セキュリティ制約および実現性評価。
6. 初期簡易トライアル結果。
7. 第3～4週で検証する1～2件の優先業務フロー。
8. 合意済みの評価指標および評価方法。

## 7. 評価指標の例

選定業務に応じて、以下の指標で効果を評価します。

- 1ケース当たりの処理時間削減率。
- 手作業またはコピー＆ペースト工程の削減数。
- 大幅な修正なしで利用可能なAI出力の割合。
- 業務ルールに対する正確性および網羅性。
- 誤りまたは情報欠落の件数と重要度。
- 業務ユーザーの操作性評価および利用意向。
- 必須となるHuman Reviewポイントの明確化。

## 8. PoC最終評価

1か月終了時に、両社で以下を評価します。

- 測定可能な業務効果を確認できた業務フロー。
- 追加データ、システム連携または方針確認が必要な業務フロー。
- AIをユーザー支援として利用するか、一部工程を自動化するか。
- 展開拡大に必要なリスク対策および統制。
- 有償パイロットまたは本番導入に向けた推奨範囲。

## 9. 前提条件

FPTは1か月間のPoCを無償で提供しますが、業務効果を適切に検証するためには、お客様側の積極的なご協力が必要です。

FPTは、AI・エンジニアリング知見、現地での業務分析、業務フロー設計および迅速なプロトタイピングを提供します。大阪ガスマーケティング様には、業務知識、代表データまたはテストケース、業務ユーザーの参加、迅速なフィードバックおよび必要な承認をご提供いただきます。

実業務へのアクセス、代表ケースまたは業務ユーザーからのフィードバックが十分でない場合、本PoCでは技術的実現性のみの確認となり、実際の業務効果を評価できない可能性があります。
