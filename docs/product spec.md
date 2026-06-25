# Healthcare Q&A Agent - Product Spec

## Overview

An AI assistant that answers healthcare questions and helps users find the right doctor. When a user describes symptoms or asks a health question, the agent explains the condition, finds relevant specialists in their area using the HealthyLinkx doctor directory, and provides a brief summary of each recommended doctor's background.

## Problem

Getting from "I have symptom X" to "here's a doctor who can help" is inherently iterative — users rarely know the right specialist upfront. They describe one symptom, remember another, refine their location, and narrow down through back-and-forth. But today's tools force them to start from scratch with every search: research a symptom, search for a specialist type, search again when the first result isn't quite right. This agent closes that gap by supporting the full conversation, not just the first question.

## What the Agent Can Do

- Answer general health questions (symptoms, conditions, treatments)
- Figure out what type of specialist a user should see based on their symptoms
- Search for doctors by specialty and location using the HealthyLinkx directory
- Provide a brief summary of each recommended doctor's history and background
- Combine all of the above into a single, helpful response
- Support follow-up questions that build on prior context — users can refine symptoms, change locations, or drill into results without repeating themselves

## Example Interactions

**Health question with doctor referral:**
> User: "I've been having recurring headaches and blurred vision. I'm in Seattle, WA."
>
> Agent: Explains possible causes (neurological, vision-related), recommends seeing a neurologist or ophthalmologist, and lists specific doctors in Seattle from the HealthyLinkx directory with a brief summary of each doctor's background and experience.

**Direct doctor search:**
> User: "Find me a cardiologist in Tacoma, WA"
>
> Agent: Returns cardiologists in the Tacoma area with a brief history of each doctor.

**General health question:**
> User: "What's the difference between a cold and the flu?"
>
> Agent: Explains the key differences in symptoms and severity. Offers to find a doctor nearby if symptoms persist.

**Symptom to specialist:**
> User: "My knee hurts when I run. Who should I see? I'm in Spokane, WA."
>
> Agent: Explains that knee pain from running is typically addressed by an orthopedist or sports medicine doctor. Lists matching specialists in Spokane along with each doctor's background summary.

**Multi-turn conversation with context carryover:**
> User: "I've been having recurring headaches and blurred vision. I'm in Seattle, WA."
>
> Agent: Explains possible causes, recommends neurologist or ophthalmologist, lists doctors in Seattle.
>
> User: "What about orthopedists?"
>
> Agent: Understands "Seattle" from the prior turn and lists orthopedists in Seattle.
>
> User: "Tell me more about the second doctor."
>
> Agent: Provides a more detailed background summary of the second doctor from the previous list.

**User correction:**
> User: "Find me a cardiologist in Seattle, WA."
>
> Agent: Lists cardiologists in Seattle.
>
> User: "Actually I meant Tacoma, not Seattle."
>
> Agent: Lists cardiologists in Tacoma instead.

**Progressive symptom disclosure:**
> User: "I've been having bad headaches."
>
> Agent: Provides general information about headaches and possible causes.
>
> User: "Also I've been feeling dizzy lately."
>
> Agent: Notes the combination of headaches and dizziness, explains what that might indicate.
>
> User: "Who should I see? I'm in Seattle, WA."
>
> Agent: Considers both symptoms together, recommends a neurologist, and lists neurologists in Seattle.

## Scope

### Included in v1
- Interactive multi-turn conversation — the user can ask follow-up questions that build on prior context
- Context carryover — details like location, symptoms, and doctor lists carry forward across turns so the user doesn't have to repeat themselves
- In-memory conversation history — history lives for the duration of the CLI session and is discarded on exit
- Conversation history management delegated to LangChain (handles token limit truncation)
- Health Q&A powered by web search
- Doctor search by specialty and location via HealthyLinkx
- Brief summary of each recommended doctor's history
- Combined answers that explain the condition and recommend doctors
- Command-line interface with an interactive prompt loop:
  - Welcome message on startup explaining what the agent does and how to exit
  - Prompt indicator: `> `
  - Exit with "exit", "quit", or Ctrl+C
  - Empty input is ignored (re-displays the prompt)
- Context carryover is always-on — details from earlier turns (location, symptoms, doctor lists) remain available unless the user explicitly corrects them
- Single-question mode preserved for backwards compatibility: `./infra/run.sh "question"` prints the answer and exits without entering the interactive loop
- **Known limitation:** conversation history is not truncated in v1 — very long sessions may exceed the LLM's context window and fail. For typical CLI usage (under ~20 turns) this is unlikely to be an issue. A future version should add truncation via LangGraph's `trim_messages`, with the agent gracefully asking the user to repeat information rather than silently failing
- The agent may proactively recommend a doctor when the question is better answered with a specialist recommendation, but does not always suggest one

### Not included in v1
- Persistent conversation history across sessions — history is in-memory only
- User accounts or saved preferences
- Appointment booking
- Insurance or cost information

## Success Criteria

- Given symptoms, the agent recommends the right type of specialist
- The agent finds real doctors from the HealthyLinkx directory when relevant
- Each recommended doctor includes a brief background summary
- Answers combine health information with doctor recommendations naturally
- Follow-up questions resolve correctly against prior context — the user doesn't need to repeat information already provided
- Conversations feel natural across multiple turns, including corrections, refinements, and drill-downs
- Responses arrive within 15 seconds for simple queries, 30 seconds for doctor searches with background lookups (per turn, not per session)

## Acceptance Tests

### Symptom-based doctor recommendation
- **Given** a user describes symptoms and provides a location
- **When** the agent processes the question
- **Then** the response explains possible conditions, recommends a specialist type, lists doctors from the HealthyLinkx directory in that area, and includes a brief background summary for each doctor
- **Test**: `"I've been having recurring headaches and blurred vision. I'm in Seattle, WA."`
- **Verify**: response mentions possible conditions (neurological, vision-related), suggests a specialist type (neurologist or ophthalmologist), lists doctor names from HealthyLinkx, and includes a background sentence for at least one doctor

### Direct doctor search
- **Given** a user requests a specific specialty in a specific location
- **When** the agent processes the question
- **Then** the response lists matching doctors from the HealthyLinkx directory with a brief background summary for each
- **Test**: `"Find me a counselor in Redmond, WA"`
- **Verify**: response lists counselor names with addresses from HealthyLinkx and includes background info for each

### General health question
- **Given** a user asks a general health question without mentioning a location
- **When** the agent processes the question
- **Then** the response answers the health question without listing doctors
- **Test**: `"What's the difference between a cold and the flu?"`
- **Verify**: response explains the differences and does not list specific doctors

### Proactive doctor recommendation
- **Given** a user asks a health question where seeing a specialist would be clearly beneficial
- **When** the agent processes the question
- **Then** the response answers the health question and proactively offers to find a relevant specialist
- **Test**: `"I've been having sharp chest pains for the past week"`
- **Verify**: response explains possible causes, recommends seeing a specialist (cardiologist or ER), and offers to search for one if a location is provided

### Follow-up with context carryover
- **Given** a user has asked a question mentioning a location
- **When** the user asks a follow-up question without repeating the location
- **Then** the agent remembers the location from the earlier turn and uses it
- **Test**: in the same session, first ask `"Find me a counselor in Redmond, WA"`, then ask `"What about orthopedists?"`
- **Verify**: second response lists orthopedists in Redmond — the location carried over from the first turn

### Follow-up referencing prior results
- **Given** the agent has listed doctors in a previous response
- **When** the user asks about a specific doctor from the list (e.g., "Tell me more about the second doctor")
- **Then** the agent identifies the correct doctor from the prior response and provides more detail
- **Test**: in the same session, ask `"Find me a counselor in Redmond, WA"`, then ask `"Tell me more about the first doctor"`
- **Verify**: response provides additional detail about the first doctor from the previous list

### No context leaks across sessions
- **Given** a user has completed a conversation session
- **When** the user starts a new session
- **Then** the new session has no memory of the previous session
- **Test**: run the CLI, ask `"Find me a counselor in Redmond, WA"`, exit, start the CLI again, ask `"What about orthopedists?"`
- **Verify**: second session's response does not reference Redmond — it treats the question as standalone

### User correction updates context
- **Given** a user has established context in a prior turn (e.g., a location)
- **When** the user corrects that context (e.g., "Actually I meant Tacoma, not Seattle")
- **Then** the agent updates its understanding and uses the corrected context going forward
- **Test**: in the same session, ask `"Find me a cardiologist in Seattle, WA"`, then say `"Actually I meant Tacoma, not Seattle"`
- **Verify**: the corrected response lists cardiologists in Tacoma, not Seattle

### Progressive symptom disclosure across turns
- **Given** a user describes symptoms incrementally across multiple turns
- **When** the user asks for a specialist recommendation
- **Then** the agent considers all symptoms mentioned across prior turns, not just the latest message
- **Test**: in the same session, ask `"I've been having bad headaches"`, then `"Also I've been feeling dizzy lately"`, then `"Who should I see? I'm in Seattle, WA."`
- **Verify**: response recommends a specialist appropriate for the combined symptom picture (headaches + dizziness), not just dizziness alone

### Response time
- **Given** any user question (first turn or follow-up)
- **When** the agent processes the question
- **Then** the response is returned within 15 seconds for simple queries, 30 seconds for doctor searches with background lookups
- **Test**: measure response time for a first-turn question and a follow-up turn within the same session
- **Verify**: each individual turn meets the target — simple query under 15 seconds, doctor search under 30 seconds

## Examples of Usage

```bash
# Start an interactive session
./infra/run.sh

# Example session:
# > I've been having recurring headaches and blurred vision. I'm in Seattle, WA.
# (agent explains conditions, lists neurologists/ophthalmologists in Seattle)
# > What about orthopedists?
# (agent lists orthopedists in Seattle — location carried over)
# > Tell me more about the second doctor.
# (agent provides detailed background on the second doctor)
# > exit

# Single-question mode (backwards compatible)
./infra/run.sh "What's the difference between a cold and the flu?"
```
