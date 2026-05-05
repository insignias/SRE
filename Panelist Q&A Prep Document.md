<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Panelist Q\&A Prep Document

This document compiles likely panelist questions from the mock interview and provides concise, interview-ready answers tailored to an AWS Solutions Architect / GenAI Solutions Architect style discussion.

## Discovery and scoping

### How would you structure your discovery to understand our current product onboarding process end to end?

Start by mapping the workflow from supplier submission to product live-on-site, including systems, handoffs, wait times, manual decisions, and approval gates. Then validate that map with each stakeholder group and identify where cycle time, quality loss, and rework are highest.

### What specific questions would you ask to quantify our current lead time (supplier to live on site)?

I would ask for average, p50, p90, and worst-case onboarding times, broken down by stage, team, and product type. I would also ask where queue time happens versus actual work time, because delays are often caused more by handoffs and approvals than processing.

### How would you identify which parts of the workflow are best candidates for automation versus staying manual?

I would automate high-volume, repetitive, rules-heavy work first, especially where outputs are standardized and measurable. I would keep human review for judgment-heavy areas like brand voice, ambiguous classification, exception handling, and final approval until quality proves out.

### How would you validate that you correctly understand the roles and responsibilities of each of our teams?

I would play back the workflow in a whiteboard summary and ask each team to confirm their inputs, outputs, SLAs, and dependencies. I would also ask where they believe upstream data quality or downstream bottlenecks hurt them most.

### How do you decide whether to focus on the e-commerce front end versus back-office systems like inventory or PIM first?

I would start where the customer gets the fastest measurable business value with the lowest integration risk. If the biggest pain is time-to-publish and merchandising quality, I would begin with onboarding and catalog enrichment before expanding into downstream inventory or broader platform modernization.

## Business outcomes and phasing

### What business KPIs would you propose for phase 1 of this project?

The key phase-1 KPIs would be cycle time from supplier file received to draft ready for review, reviewer time per SKU, percentage of fields auto-populated, confidence-score acceptance rate, and publish accuracy. I would also track rework rate and how many products still require full manual handling.

### How would you define success for a phase 1 implementation here?

Success would be reducing onboarding time materially without lowering catalog quality or creating governance risk. A strong phase 1 proves that AI can generate a high-quality draft, route exceptions correctly, and let humans review in minutes instead of hours.

### If we’re currently at about a week per product, what realistic target would you set for a first phase?

I would avoid promising 30 minutes immediately. A realistic phase-1 target would be taking the process from days-to-a-week down to same day for standard SKUs, with draft generation in minutes and human review measured in under a few minutes for straightforward products.

### How would you phase this program so we don’t bet everything on a big-bang change?

I would break it into phases: first supplier ingestion and normalization, then AI-assisted enrichment, then confidence-based routing with human review, and only later automated publish. That reduces risk, creates checkpoints, and lets the team prove ROI before broad rollout.

### How would you prioritize between improving speed, improving data quality, and reducing manual effort?

I would prioritize speed and quality together, because moving faster with bad catalog data hurts conversion and trust. Manual effort reduction is important, but it should be treated as the result of better workflow design rather than the only objective.

## Architecture and service choices

### Walk me through the high-level architecture you’d propose for this solution.

Suppliers submit files through managed ingestion endpoints, the files land in durable object storage, and an event triggers processing and enrichment. The pipeline then normalizes attributes, generates draft catalog content, assigns confidence, routes for approval when needed, stores results, and finally publishes approved products through platform APIs.

### Why are you choosing object storage like S3 as the landing zone for supplier files instead of another option?

Amazon S3 is a natural landing zone because it is durable, scalable, and well integrated with event-driven processing patterns in AWS. It also works well with managed file transfer patterns and downstream workflows that trigger on object creation.[^1][^2]

### Why use event-driven processing instead of scheduled batch jobs?

An event-driven model reduces latency because processing can begin as soon as a file arrives rather than waiting for a polling cycle. AWS Lambda is explicitly designed to support event-driven architectures and can be triggered directly by Amazon S3 notifications.[^2][^3]

### What alternatives to Lambda would you consider for the processing layer, and when?

Lambda is a good fit for lightweight, bursty, event-driven processing, especially early on. If workloads become long-running, require custom runtimes, or need more orchestration control, I would consider containers or workflow services while still preserving the same event-driven ingestion model.[^3][^2]

### Why would you pick DynamoDB for storing product and catalog metadata rather than a relational database?

If the access pattern is mostly key-based retrieval of product records, generated fields, status, and confidence metadata, a NoSQL model can be efficient and operationally simple. If there are strong relational requirements, complex joins, or transactional dependencies across many entities, I would reevaluate and consider a relational service instead.

### In what scenarios would you recommend RDS or Aurora instead of DynamoDB for this workload?

I would choose RDS or Aurora if the domain model depends on relational consistency, complex querying across many tables, or strong transactional workflows. That is especially true if the catalog process must integrate tightly with existing relational systems of record.

### How would you integrate our existing e-commerce platform APIs into this architecture?

I would treat the commerce platform as the final system of action and integrate through versioned APIs after approval gates are complete. That keeps the ingestion and enrichment pipeline decoupled from publishing and makes rollback or retry safer.

## Ingestion and Transfer Family

### How would you support different supplier ingestion patterns in one design?

I would expose multiple controlled entry points: API for mature suppliers, managed SFTP for legacy partners, and potentially a simple upload UI for manual cases. All paths would normalize into the same landing zone and downstream pipeline so the back end stays consistent.

### Why would you use AWS Transfer Family for SFTP rather than running our own SFTP server on EC2?

AWS Transfer Family is a managed service for file transfer protocols including SFTP, which reduces infrastructure management compared with running and patching a custom server. It is designed to work with AWS storage services and removes much of the undifferentiated operational overhead.[^4][^5][^1]

### From the supplier’s point of view, how does a managed SFTP endpoint on AWS look different from what they have today?

From the supplier side, it can still look like a normal SFTP endpoint with credentials and a familiar client workflow. The difference is that the service is managed on the back end and can be connected directly to AWS storage and workflows.[^6][^1]

### How would you handle suppliers who cannot or will not change their current format or protocol?

I would not block the business on standardization. I would build a normalization layer that accepts supplier-specific formats first, then gradually introduce preferred patterns and incentives for cleaner integrations over time.

## AI, Bedrock, agents, and workflows

### Where exactly would you introduce AI in this pipeline, and where would you keep things deterministic?

I would use AI where interpretation or generation is useful, such as title creation, description drafting, attribute completion, keyword generation, and potentially image selection support. I would keep ingestion, schema checks, routing, approval logic, and publishing deterministic wherever possible.[^7][^8]

### What concrete use cases would you prioritize for generative AI here?

The first use cases would be draft titles, descriptions, searchable keywords, attribute normalization, and missing-field completion. I would be more cautious about pricing and market analysis because those can affect margin and usually need tighter governance.[^8][^7]

### What models or capabilities from Amazon Bedrock would you use, and why?

Amazon Bedrock provides managed foundation model capabilities and agent-related options that can support generation and tool use without building everything from scratch. I would choose capabilities based on whether the need is simple content generation, retrieval-backed reasoning, or more complex orchestration.[^9][^7][^8]

### When would you prefer a simple workflow over an agent-based approach?

I would start with a workflow when the sequence is fixed, approval rules are known, and the tasks are predictable. I would only move toward agents if the system needs dynamic tool selection, flexible reasoning across changing tasks, or more autonomous decision-making.[^7][^8]

### Why would we need Bedrock AgentCore specifically, and what does it give us beyond just calling models from Lambda?

Bedrock AgentCore is positioned as managed infrastructure for building and operating AI agents at scale. That can be valuable if the design genuinely needs agent capabilities, but for phase 1 I would still justify it carefully against a simpler workflow approach before introducing extra architectural complexity.[^8][^9]

### How would you design the quality or confidence scoring mechanism for AI-generated content?

I would score outputs against defined criteria such as completeness, consistency with source attributes, policy compliance, and similarity to approved historical patterns. That score should be measurable, auditable, and tuned over time using reviewer feedback.

### How would you set thresholds for auto-approval versus human review? Who should own those thresholds?

I would begin conservatively, with high thresholds for auto-approval and broad review coverage until the system proves quality. Merchandising, compliance, and product owners should jointly own the thresholds, because the tradeoff is business risk, not just technical confidence.

## Human in the loop

### How would you keep our existing experts in the loop without overwhelming them?

I would turn their role from full manual creation into rapid review and exception handling. The system should present source data, generated recommendations, and reasons for low confidence so reviewers only focus on what actually needs judgment.

### What parts of the process would still require human judgment in your design?

Brand-sensitive wording, ambiguous classifications, pricing exceptions, edge-case imagery choices, and final governance decisions would still benefit from human oversight. The goal is not to remove expertise, but to reserve it for higher-value decisions.

### How would you design the human review UI so reviewers can quickly approve or fix AI-generated suggestions?

I would present side-by-side source inputs and generated outputs, highlight low-confidence fields, and allow inline edits with one-click approve or reject actions. I would also capture reviewer corrections as feedback signals for continuous improvement.

### How would you measure and improve the AI’s performance over time using feedback from our teams?

I would track accept-without-edit, accept-with-edit, reject, and common correction categories. That creates a feedback loop to refine prompts, guardrails, thresholds, and any retrieval or business-rule logic.

## Security and data protection

### How would you protect our secret sauce in this design?

I would isolate sensitive data paths, apply least-privilege access, encrypt data in transit and at rest, and avoid exposing proprietary logic outside controlled boundaries. I would also separate raw supplier data, derived pricing intelligence, and publish-ready outputs by access policy and audit them closely.

### How does AWS ensure encryption in transit and at rest for services like Transfer Family, S3, and DynamoDB?

AWS documentation for Transfer Family describes managed file transfer integrated with AWS services, and S3-based ingestion patterns commonly support secure storage and controlled processing paths. The design should enforce encryption in transit and at rest across the ingestion and processing flow.[^1][^4]

### What specific controls would you put in place so that our proprietary pricing and market analysis data is not leaked by AI systems?

I would restrict which data is sent to models, minimize sensitive context in prompts, log and review access, and apply strict IAM and network boundaries around enrichment services. I would also keep sensitive business logic outside model prompts where possible and use approval gates before any external action.[^7][^8]

### How does Amazon Bedrock handle data isolation and ensure our prompts or completions aren’t used to train public models?

This should be answered directly from current Bedrock service terms during a real customer discussion, but the broader point is that managed Bedrock capabilities are designed for enterprise AI use on AWS. The right approach in the meeting is to answer precisely from service documentation and align that with the customer’s security review process.[^9][^8][^7]

### What network and identity controls would you recommend for this architecture?

I would use least-privilege IAM roles, private connectivity where supported, strong key management, and service-to-service access boundaries. I would also separate environments and apply detailed logging, alerting, and audit trails around supplier ingress and approval actions.

### How would you address the customer’s concern about AI vendors being hacked in the news?

I would acknowledge the concern directly, avoid hand-waving, and explain the concrete controls in the target architecture. I would also position the first phase as low-risk and measurable, with limited scope and clear data-handling boundaries.

## Cost, risk, and proof of concept

### How would you estimate the cost of this solution across storage, compute, data transfer, and AI inference?

I would estimate cost by expected supplier file volume, object storage growth, processing frequency, average model calls per product, review volume, and publish volume. Then I would present a range with assumptions so the customer can see what actually drives spend.[^5][^2][^8]

<div align="center">⁂</div>

[^1]: https://docs.aws.amazon.com/transfer/latest/userguide/what-is-aws-transfer-family.html

[^2]: https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html

[^3]: https://docs.aws.amazon.com/lambda/latest/dg/concepts-event-driven-architectures.html

[^4]: https://docs.aws.amazon.com/transfer/

[^5]: https://aws.amazon.com/aws-transfer-family/

[^6]: https://docs.aws.amazon.com/transfer/latest/userguide/getting-started.html

[^7]: https://docs.aws.amazon.com/bedrock/latest/userguide/agents-how.html

[^8]: https://aws.amazon.com/bedrock/agentcore/

[^9]: https://docs.aws.amazon.com/bedrock-agentcore/

