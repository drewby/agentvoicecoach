# VoiceCoach

**MVP PRODUCT BRIEF**
**AI-Powered Voice Simulation for Customer Service Training**

| | |
|---|---|
| **Domain** | Retail Customer Service |
| **Status** | Proposed — Seeking User Acceptance |
| **Date** | March 2026 |
| **Version** | 1.1 |

---

## 1. Executive Summary

VoiceCoach is a voice-based simulation tool that trains retail customer service representatives through realistic AI-powered conversations. A trainee selects a scenario, conducts a live voice conversation with an AI customer, and then receives automated coaching feedback grounded in company procedures.

Both the simulation and coaching are driven by a shared employee manual that defines how the company expects representatives to handle every type of interaction. The AI customer uses the manual to test whether the trainee follows correct procedures, while the coaching agent cites specific manual sections when delivering feedback. This ensures training is consistent, auditable, and directly tied to actual company standards.

This document defines the minimum viable product (MVP) scope for a user acceptance test. The goal is to validate the core training loop — scenario selection, voice simulation, and procedure-grounded coaching — before investing in a full production build.

---

## 2. Product Overview

### How It Works

The product follows a three-step loop designed to be completed in under ten minutes per session:

| Step | Action | Description |
|------|--------|-------------|
| **1** | **Select Scenario** | The trainee picks from three difficulty-graded scenarios, each presenting a different customer persona and problem type. |
| **2** | **Voice Simulation** | The trainee speaks with an AI customer in real time. The AI stays in character, probes whether the trainee follows company procedures, and the full transcript is captured. |
| **3** | **Coaching Review** | A separate AI evaluator analyzes the transcript against the employee manual and a coaching rubric, delivering feedback that cites specific company procedures. |

### Two-Agent Architecture

The product uses two independent AI agents that share a common knowledge base: the employee manual. Separating the agents allows each to be tuned and iterated on independently, while the shared manual ensures both are aligned on what "correct" looks like.

**Simulation Agent**
Plays the AI customer. Maintains persona consistency and responds naturally to the trainee.

> **Manual usage:** Uses the employee manual to deliberately create situations that test whether the trainee follows correct procedures. For example, if the manual requires reps to verify order numbers before processing returns, the AI customer will wait to see if the trainee asks — and if they don't, the customer won't volunteer it. The actor can also introduce edge cases from the manual (e.g., asking for a refund on a final-sale item, requesting a price match) to test deeper procedural knowledge.

**Coaching Agent**
Receives the completed transcript after the simulation ends. Evaluates the trainee's performance against a rubric and the employee manual.

> **Manual usage:** Grounds every piece of feedback in specific manual sections. Instead of generic advice like "you should have shown more empathy," the coach says "Per §2.1 (Greeting & Acknowledgment), you should lead with the customer's name and acknowledge their concern before moving to troubleshooting." This makes feedback actionable and traceable to a standard the trainee can review independently.

---

## 3. Employee Manual (Abridged for MVP)

The following is the employee manual used by both agents. In production, this would be sourced from the company's actual training documentation. For the MVP, we use a fictional but realistic manual for Northfield Home & Living. Both agents receive the full manual in their system prompts.

### §1 — Core Service Standards

> **§1.1 — Greeting Protocol**
>
> Every interaction must begin with a greeting that includes:
> - a) A welcome statement ("Thank you for calling Northfield Home & Living")
> - b) The representative's name
> - c) An offer to help ("How can I help you today?")
>
> If the customer provides their name, use it throughout the call. If not provided, do not ask — use "sir" or "ma'am."

> **§1.2 — Active Listening & Acknowledgment**
>
> Before proposing any solution, the rep must:
> - a) Restate the customer's issue in their own words to confirm understanding
> - b) Acknowledge the customer's emotion ("I understand that's frustrating")
>
> Never jump directly to a solution or policy statement without acknowledgment first. Customers who feel heard are 3x more likely to accept a resolution.

> **§1.3 — Closing Protocol**
>
> Every call must end with:
> - a) A summary of all actions taken and next steps
> - b) Confirmation that the customer has no additional questions
> - c) A thank-you statement

### §2 — Returns & Exchanges

> **§2.1 — Return Windows**
>
> Standard return windows by category:
> - Kitchen & Home appliances: 30 days from delivery
> - Bath & Textiles: 90 days (must be unused with tags)
> - Decor (rugs, art): 14 days (must be unused and in original packaging)
> - Accessories: 30 days
>
> **All returns require an order number. The rep must verify the order number before discussing return eligibility. Never process a return without verification.**

> **§2.2 — Damaged / Defective Items**
>
> If the customer reports a damaged or defective item:
> - a) Verify the order number and item
> - b) Determine if the item is within the return window → full replacement at no cost
> - c) If outside the return window, check warranty coverage → warranty replacement
> - d) Always offer a prepaid return label for the defective item
>
> **Reps may NOT offer refunds for out-of-window items regardless of damage. Warranty replacement is the maximum resolution. Escalate to a supervisor only if the customer explicitly and repeatedly requests one.**

> **§2.3 — Wrong Item Received**
>
> If the customer received the wrong item (wrong color, size, or product):
> - a) Apologize for the error
> - b) Ship the correct item immediately — do not wait for the return of the wrong item
> - c) Provide a prepaid return label for the incorrect item

### §3 — Escalation & De-escalation

> **§3.1 — De-escalation Framework**
>
> When a customer becomes upset, follow the HEAT framework:
> - **H — Hear:** Let the customer express their frustration without interrupting.
> - **E — Empathize:** Acknowledge their specific emotion and situation.
> - **A — Apologize:** Offer a genuine apology for the experience, not a conditional one ("I'm sorry you feel..." is not acceptable).
> - **T — Take action:** Propose a concrete resolution. Never leave the customer waiting for next steps.

> **§3.2 — Goodwill Gestures**
>
> Reps are authorized to offer the following goodwill gestures without supervisor approval:
> - Store credit up to $20
> - Free expedited shipping on a replacement order
> - Waived return shipping fee
>
> **Goodwill gestures should be offered proactively when the customer has been significantly inconvenienced. Do not wait for the customer to demand compensation. Gestures above $20 require supervisor approval.**

> **§3.3 — Supervisor Escalation**
>
> Transfer to a supervisor only when:
> - a) The customer explicitly and repeatedly requests a supervisor (a single mention is not sufficient — attempt resolution first)
> - b) The resolution requires authority beyond the rep's limit (e.g., goodwill over $20, policy exceptions)
>
> Before transferring, summarize the situation to the customer and assure them the supervisor will have full context. Never use a supervisor transfer as a way to avoid a difficult conversation.

### §4 — Product Knowledge Requirements

> **§4.1 — Product Recommendations**
>
> When recommending a product:
> - a) Ask at least one clarifying question about the customer's needs before recommending
> - b) Reference specific product features relevant to the customer's stated need
> - c) Mention warranty coverage and return window proactively

> **§4.2 — Shipping & Loyalty**
>
> Standard shipping: $6.99. Free shipping on orders over $75. Always mention the free shipping threshold when the customer's order is close to qualifying.
>
> Loyalty program: 1 point per dollar spent. 100 points = $5 reward. Points are retained on exchanges but forfeited on refunds. If a customer asks about loyalty impact, always provide a clear answer.

### §5 — Prohibited Actions

> **§5.1 — Things Reps Must Never Do**
> - Never promise a refund for out-of-window purchases
> - Never blame the customer for a defective product
> - Never share personal opinions about product quality ("Yeah, we get a lot of complaints about that one")
> - Never process a return or exchange without verifying the order number first
> - Never offer a goodwill gesture exceeding $20 without supervisor approval
> - Never use conditional apologies ("I'm sorry you feel that way")

---

## 4. Simulated Product Catalog

The simulation uses a fictional retail brand, **Northfield Home & Living**. The AI customer and trainee both operate within the context of this catalog. The product catalog is provided to the simulation agent as part of its knowledge base.

| SKU | Product | Price | Category | Notes |
|-----|---------|-------|----------|-------|
| NF-BL-4200 | **Summit Blender Pro** | $89.99 | Kitchen | 60-day return. 2-yr warranty. Glass carafe; replacement carafes available ($24.99). |
| NF-CF-1100 | **BrewMaster Drip Coffee Maker** | $64.99 | Kitchen | 30-day return. 1-yr warranty. Reusable filter included; paper filters sold separately. |
| NF-VC-3300 | **QuietClean Upright Vacuum** | $199.99 | Home | 30-day return. 3-yr warranty. HEPA filter. Belt replacement every 12 months (~$12.99). |
| NF-TW-7500 | **CloudSoft Bath Towel Set (4-pk)** | $49.99 | Bath | 90-day return. 100% Egyptian cotton. Colors: White, Sand, Slate, Ocean. |
| NF-LP-6200 | **Edison Desk Lamp** | $39.99 | Lighting | 30-day return. LED, USB-C charging port. Dimmable with 3 color temperatures. |
| NF-RG-2200 | **Heritage Wool Area Rug (5x7)** | $149.99 | Decor | 14-day return (must be unused). Dry clean only. Available in Ivory and Charcoal. |
| NF-SS-8100 | **Arctic Steel Water Bottle (24oz)** | $29.99 | Accessories | 30-day return. Double-wall insulated. Lifetime warranty on insulation defects. |
| NF-CK-4500 | **ProEdge Knife Set (8-pc)** | $119.99 | Kitchen | 30-day return. 5-yr warranty. Includes sharpening steel. Full tang stainless steel. |

*Store policies relevant to all scenarios: free shipping on orders over $75, standard shipping is $6.99, and loyalty members earn 1 point per dollar spent (100 points = $5 reward).*

---

## 5. Training Scenarios

Each scenario defines the AI customer's persona, backstory, goal, and behavioral boundaries. The trainee sees only a difficulty label and one-line description. The AI customer uses the employee manual to test specific procedures, noted under "Manual Sections Tested" for each scenario.

### Scenario 1: Simple Product Inquiry (Easy)

> **Customer Persona:** Sarah, a friendly first-time customer browsing for a gift for her partner who recently started a home coffee hobby.
>
> **Goal:** Get a product recommendation for the BrewMaster Coffee Maker, ask about filter compatibility, and confirm shipping costs.
>
> **Behavior:** Polite, patient, slightly indecisive. Will ask 2–3 clarifying questions. Easily satisfied by a confident, knowledgeable answer.
>
> **Manual Sections Tested:** §1.1 (Greeting Protocol), §1.3 (Closing Protocol), §4.1 (Product Recommendations — asks a clarifying question before recommending), §4.2 (Shipping & Loyalty — mentions free shipping threshold).
>
> **Actor Strategy:** Sarah will not volunteer what she's looking for immediately — she'll say "a gift for my partner" and wait to see if the rep asks a clarifying question per §4.1 before recommending. She'll also mention her order will be around $65 to see if the rep proactively mentions the $75 free shipping threshold.

#### Example Conversation Script

*[Call begins]*

**AI Customer:** Hi! I'm looking for a gift for my partner.

*[Testing §4.1 — will the rep ask a clarifying question, or jump to a recommendation?]*

**Trainee:** Welcome to Northfield Home & Living! My name is Alex, how can I help you find the right gift today? Can you tell me a bit about what your partner is into?

*[Trainee follows §1.1 (greeting) and §4.1 (clarifying question) — good]*

**AI Customer:** He's just getting into making coffee at home. Nothing fancy yet, but he's been watching videos about pour-overs and drip brewing.

**Trainee:** That's great! For someone just starting out, I'd recommend our BrewMaster Drip Coffee Maker. It's $64.99, really beginner-friendly, and it comes with a reusable filter built in so he doesn't need to buy anything extra to get started. It also has a 1-year warranty.

*[Testing §4.2 — order is $64.99, will the rep mention the $75 free shipping threshold?]*

**AI Customer:** Oh nice, reusable filter? So he wouldn't need paper ones?

**Trainee:** Exactly — the reusable filter is included. If he prefers paper filters later for a cleaner taste, we sell those separately, but they're totally optional. And I should mention — shipping is $6.99, but if you add anything else to bring your total over $75, shipping becomes free. We have some great coffee accessories that would pair well.

*[Trainee proactively mentions threshold — follows §4.2]*

**AI Customer:** Good to know! I think I'll just go with the coffee maker for now. Thanks so much!

**Trainee:** Great choice! So to confirm, that's one BrewMaster Drip Coffee Maker at $64.99 with $6.99 standard shipping. You'll get a confirmation email with tracking. Is there anything else I can help you with today?

*[Trainee follows §1.3 (closing summary and check) — good]*

**AI Customer:** Nope, that's it. Thanks!

**Trainee:** Thank you for shopping with Northfield! I hope your partner loves it. Have a great day!

*[Call ends — transcript sent to coaching agent]*

---

### Scenario 2: Multi-Issue Order Problem (Medium)

> **Customer Persona:** David, a returning customer and loyalty member. He placed an order three days ago. Not angry but mildly frustrated because multiple things went wrong.
>
> **Goal:** He ordered the QuietClean Vacuum and CloudSoft Towel Set. The vacuum arrived with a cracked handle, and the towels were the wrong color (received Sand, ordered Ocean). He wants the vacuum replaced and the towels exchanged.
>
> **Behavior:** Business-like, expects efficiency. Will reveal issues one at a time (vacuum first, then towels). Will ask about loyalty points.
>
> **Manual Sections Tested:** §1.2 (Active Listening), §2.1 (Return Windows — order verification), §2.2 (Damaged Items), §2.3 (Wrong Item), §4.2 (Loyalty — points on exchanges), §1.3 (Closing summary).
>
> **Actor Strategy:** David will offer his order number unprompted, but will only mention the vacuum issue first. He'll wait to see if the rep asks "Is there anything else?" before revealing the towel problem. This tests whether the rep checks for additional issues. He'll also ask about loyalty points to test §4.2 knowledge.

#### Example Conversation Script

*[Call begins]*

**AI Customer:** Hi, I got my order a couple days ago and there are some problems. My order number is NF-20260318.

**Trainee:** Thank you for calling Northfield Home & Living, David. I'm sorry to hear that. Let me pull up order NF-20260318 right now. I can see your QuietClean Vacuum and CloudSoft Towel Set. Can you tell me what's going on?

*[Testing §1.2 — does the rep restate and acknowledge before solving?]*

**AI Customer:** Yeah, the vacuum handle is cracked. Looks like shipping damage.

**Trainee:** I'm really sorry about that — receiving a damaged vacuum is definitely not the experience you should have. So the handle on the QuietClean is cracked, and it looks like it happened during shipping — is that right?

*[Trainee restates issue and acknowledges emotion — follows §1.2]*

**AI Customer:** That's right.

**Trainee:** Since this is within the 30-day return window and it's shipping damage, I'll send a brand new replacement out to you right away at no charge. You'll get a prepaid return label for the damaged one. The replacement should arrive in 3–5 business days. Is there anything else with the order?

*[Rep proactively asks about additional issues — good]*

**AI Customer:** Actually yes — the towels are wrong. I ordered Ocean and got Sand.

**Trainee:** I apologize for that mix-up. Per our policy on wrong items, I'll ship the Ocean set out immediately — we won't wait for the Sand ones to come back first. I'll include a prepaid return label for those as well. Both replacements can go out in the same shipment.

*[Follows §2.3 — ships correct item immediately without waiting for return]*

**AI Customer:** Good. One more thing — does any of this affect my loyalty points?

**Trainee:** Great question. Since these are exchanges rather than refunds, your loyalty points stay exactly as they are. No changes at all.

*[Correct per §4.2]*

**AI Customer:** Alright, that's everything. Thanks.

**Trainee:** Of course, David. So to recap: a replacement QuietClean Vacuum and an Ocean CloudSoft Towel Set are both shipping out today, you'll receive prepaid return labels for the damaged vacuum and the Sand towels, and your loyalty points are unaffected. You'll get a confirmation email shortly. Anything else?

*[Follows §1.3 — closing summary with all action items]*

**AI Customer:** No, that covers it. Appreciate it.

**Trainee:** Thank you for your patience, David, and for being a loyal Northfield customer. Have a great day!

*[Call ends — transcript sent to coaching agent]*

---

### Scenario 3: Angry Customer Escalation (Hard)

> **Customer Persona:** Karen, a very frustrated customer. She purchased the ProEdge Knife Set five weeks ago as a wedding gift. The recipient found a chipped blade on first use. Karen is past the 30-day return window.
>
> **Goal:** She wants a full refund. The rep cannot offer a refund (past return window, per §2.1) but can offer a warranty replacement (per §2.2). Karen will escalate emotionally before accepting or demanding a manager.
>
> **Behavior:** Starts annoyed, escalates to angry when told a refund isn't possible. Will interrupt, repeat complaints, question product quality, and threaten bad reviews. Can be de-escalated by the HEAT framework (§3.1) and a proactive goodwill gesture (§3.2).
>
> **Manual Sections Tested:** §1.2 (Acknowledgment), §2.1 (Return Windows), §2.2 (Defective — warranty path), §3.1 (HEAT de-escalation), §3.2 (Goodwill — within $20 limit), §3.3 (Escalation — should not transfer prematurely), §5.1 (Prohibited — must not promise a refund or blame customer).
>
> **Actor Strategy:** Karen will test several prohibited actions: she'll push for a refund (§5.1 says reps must not promise one), she'll say "maybe I should talk to a manager" once to see if the rep transfers prematurely (§3.3 says a single mention is not sufficient — attempt resolution first). She'll also wait to see if the rep offers a goodwill gesture proactively or only after being pressured.

#### Example Conversation Script

*[Call begins]*

**AI Customer:** Yeah, hi. I need to talk to someone about a knife set I bought. The ProEdge set? One of the blades came chipped right out of the box. This was a wedding gift. Extremely embarrassing.

**Trainee:** Thank you for calling Northfield Home & Living. I'm Alex, and I'm really sorry to hear that — I completely understand how frustrating that must be, especially for a gift. Let me look into this for you right away. Can I have your order number?

*[Follows §1.1 (greeting) and begins §1.2 (acknowledgment)]*

**AI Customer:** It's NF-20260214. I want a full refund.

**Trainee:** I've pulled up your order. I can see the ProEdge Knife Set purchased on February 14th. A chipped blade on a wedding gift — I completely agree that shouldn't have happened, and I'm sorry for the experience. I do need to let you know that the purchase is past our 30-day return window for a refund. I know that's not what you were hoping to hear.

*[Pause and re-acknowledge before pivoting — applying HEAT: Hear + Empathize]*

**Trainee:** Here's what I can do: this set carries a 5-year warranty, and a chipped blade is fully covered. I can have a brand new replacement set shipped today with expedited delivery at no cost, so the recipient gets a perfect set within 2 business days. I'd also like to add a $15 store credit to your account for the inconvenience.

*[Follows §2.2 (warranty replacement) + §3.2 (proactive goodwill under $20 limit)]*

*[Escalation point — customer becomes angry]*

**AI Customer:** Are you kidding me? I spent $120 on a defective product and you can't give me my money back? This is ridiculous. Maybe I should just talk to a manager.

*[Testing §3.3 — single mention of manager. Will the rep transfer prematurely?]*

**Trainee:** I completely understand your frustration, and I want to make sure we get this resolved for you. I'm authorized to handle this and I want to make it right. The replacement set is the exact same quality — these are full-tang stainless steel blades built to last, so what happened is genuinely unusual. With the expedited replacement and the $15 credit, the recipient will have a perfect set by Thursday and you'll have credit for a future purchase. Can I go ahead and set that up?

*[Rep does not transfer — correct per §3.3. Reinforces product quality per §4.1]*

*[De-escalation — customer begins to soften]*

**AI Customer:** I mean… I still think I should get a refund. But fine, let's do the replacement. If this one has any issues though, I expect a full refund.

**Trainee:** I'm processing the replacement now. So to recap: a brand new ProEdge Knife Set ships today with 2-day expedited delivery, a $15 store credit is on your account immediately, and you'll get a prepaid return label for the defective set. You'll have a confirmation email with tracking within the hour. Is there anything else I can help with?

**AI Customer:** No, that's it.

**Trainee:** Thank you for your patience, Karen, and I'm sorry again for the trouble. We appreciate your business. Have a good day.

*[Call ends — transcript sent to coaching agent]*

---

## 6. Coaching Evaluation: Example Output

The following is an example of the coaching agent's evaluation after analyzing the Scenario 3 (Hard) transcript. The coach grounds every observation in a specific manual section so the trainee can review the relevant procedure independently.

### Performance Scores

| Category | Score | Summary |
|----------|-------|---------|
| **Greeting Protocol** | **10/10** | §1.1 — Complete greeting with name, welcome, and offer to help. Used customer's name throughout. |
| **Active Listening** | **9/10** | §1.2 — Restated the issue and acknowledged emotion before proposing a solution. Strong acknowledgment of the gift context. |
| **Product Knowledge** | **9/10** | §4.1 — Correctly cited 5-year warranty and proactively mentioned full-tang construction to reinforce quality. |
| **De-escalation (HEAT)** | **10/10** | §3.1 — Textbook HEAT execution. Heard the frustration, empathized with the gift context, apologized genuinely, and took immediate action. |
| **Goodwill Gesture** | **10/10** | §3.2 — Offered $15 credit proactively without being pressured. Within the $20 authorized limit. |
| **Escalation Handling** | **10/10** | §3.3 — Customer mentioned a manager once. Rep correctly did not transfer and continued to resolve. Exactly per policy. |
| **Policy Compliance** | **10/10** | §2.2, §5.1 — Did not promise a refund for the out-of-window purchase. Correctly offered warranty replacement. |
| **Closing Protocol** | **9/10** | §1.3 — Strong recap of all actions and next steps. Minor note: could have explicitly confirmed the return label detail. |
| **Overall** | **9.6/10** | Excellent performance. Trainee demonstrated strong procedural compliance and de-escalation skills. |

### Interactive Coaching Dialogue

After the scores are presented, the coaching agent walks through the transcript interactively, citing specific manual sections.

*[Coaching session begins]*

**Coach:** Great work on that call — 9.6 overall. Let's walk through the highlights and a couple areas to sharpen. First, your opening was textbook §1.1: you gave your name, a welcome, and an offer to help. You also immediately acknowledged the gift context, which falls under §1.2. That combination — greeting plus emotional acknowledgment in the same breath — set the right tone for the entire call.

**Coach:** Now, the critical moment: when Karen asked for a refund and you had to say no. You handled this well by pausing to acknowledge her frustration before pivoting to the warranty option. That's exactly the HEAT framework from §3.1 — Hear, Empathize, Apologize, Take Action. One refinement: you said "I do need to let you know that the purchase is past our 30-day return window." That's accurate per §2.1, but consider softening the delivery by leading with what you can do before stating the limitation. Something like: "I want to make sure we take care of this. The set has a 5-year warranty that fully covers this, so here's what I'd like to do…" Then if the customer pushes back on why not a refund, you explain the window. That way the customer hears the solution before the "no."

**Coach:** The moment Karen mentioned a manager was your hardest test. Per §3.3, a single mention does not require a transfer — you should attempt resolution first. You did exactly that. You stayed calm, restated your authority, and reinforced the solution. That was a strong read of the policy. If she had asked a second or third time, then a transfer would have been appropriate.

**Coach:** Your goodwill gesture was well-timed. Per §3.2, you're authorized up to $20 without supervisor approval, and you offered $15 proactively — before Karen escalated further. The manual specifically says reps should offer goodwill proactively when the customer has been significantly inconvenienced. You did that perfectly.

**Coach:** Last note on your closing: your recap covered the replacement, the store credit, and the expedited shipping — all good per §1.3. You could tighten it slightly by also explicitly confirming "you'll get a prepaid return label in that email for the defective set." That small addition ensures the customer knows every single action item without having to re-read the email.

*[Coaching session ends]*

### Key Improvement Areas

1. **Lead with the solution, follow with the limitation.** When delivering a policy constraint (§2.1), present the alternative resolution before stating the restriction. Let the customer hear "here's what I can do" before "here's what I can't."
2. **Tighten closing recaps.** Per §1.3, include every action item in a single summary sentence at the end — replacement, return label, credit, and timeline. Leave nothing for the customer to wonder about.

---

## 7. MVP Scope & Technical Approach

### In Scope for MVP

- Web-based single-page application (no mobile app required for user acceptance testing)
- Three pre-built scenarios with fixed difficulty labels (Easy, Medium, Hard)
- Full employee manual included in both agent system prompts as shared knowledge base
- Voice input via browser Web Speech API (speech-to-text) with a text fallback option
- AI voice output via browser speech synthesis or a TTS API for the customer persona
- Real-time transcript display during the simulation
- Post-call coaching evaluation with scores grounded in manual section references
- Static fictional product catalog (Northfield Home & Living, 8 products)

### Out of Scope for MVP

- User authentication and accounts
- Persistent session history or progress tracking
- Manager dashboards or aggregate reporting
- Custom scenario creation or manual editing interface
- Integration with real product catalogs, CRM, or HR systems
- Multi-language support

### Architecture

The technical build is intentionally minimal. The simulation and coaching agents are both LLM calls with carefully designed system prompts. The product catalog, scenario definitions, and employee manual are static content embedded in the application. No database, no backend services beyond the LLM API.

| Component | Approach |
|-----------|----------|
| **Frontend** | Single-page web app (React or plain HTML). Three screens: scenario picker, simulation view, coaching results. |
| **Voice Input** | Browser Web Speech API (SpeechRecognition) for speech-to-text. Text input as fallback. |
| **Voice Output** | Browser SpeechSynthesis API or a TTS service (ElevenLabs, Deepgram) for natural delivery. |
| **Employee Manual** | Static document included in both agent system prompts. Same manual, two different instructions on how to use it (actor tests it; coach cites it). |
| **Simulation Agent** | LLM API call with system prompt defining persona, scenario rules, product catalog, employee manual, and instructions to test the trainee's procedural compliance. |
| **Coaching Agent** | Separate LLM API call receiving the transcript, employee manual, and a scoring rubric. Returns structured evaluation with manual section citations. |
| **Data Storage** | None for MVP. Transcript lives in-memory during the session only. |

---

## 8. Key Risks for User Acceptance

**Voice naturalness:** The primary risk is experiential. If the AI customer feels robotic or predictable, trainees will disengage. This can only be evaluated through direct user testing, which is exactly what this MVP is for.

**Manual coverage:** The abridged manual covers the key procedures for these three scenarios. If testers encounter situations not covered by the manual, the coaching agent may fall back to generic advice. This will inform what sections need to be added for production.

**Procedural testing depth:** The simulation agent's ability to test manual compliance depends on prompt quality. If the actor doesn't probe deeply enough, the coaching feedback loses value. Prompt tuning during the acceptance test will be critical.

---

## 9. Recommended Next Steps

1. Approve this brief and align on scope boundaries.
2. Build the MVP (estimated: 1–2 weeks for a functional prototype).
3. Recruit 5–10 customer service reps for a user acceptance test.
4. Run each tester through all three scenarios and collect structured feedback.
5. Evaluate: decide to proceed, iterate, or pivot based on tester feedback.