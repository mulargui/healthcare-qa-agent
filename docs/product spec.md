# Healthcare Q&A Agent - Product Spec

## Overview

An AI assistant that answers healthcare questions and helps users find the right doctor. When a user describes symptoms or asks a health question, the agent explains the condition, finds relevant specialists in their area using the HealthyLinkx doctor directory, and provides a brief summary of each recommended doctor's background.

## Problem

Getting from "I have symptom X" to "here's a doctor who can help" requires two separate steps today: researching the condition online, then searching for the right type of specialist. This agent closes that gap in a single conversation.

## What the Agent Can Do

- Answer general health questions (symptoms, conditions, treatments)
- Figure out what type of specialist a user should see based on their symptoms
- Search for doctors by specialty and location using the HealthyLinkx directory
- Provide a brief summary of each recommended doctor's history and background
- Combine all of the above into a single, helpful response

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

## Scope

### Included in v1
- Single question, single answer (no back-and-forth conversation)
- Health Q&A powered by web search
- Doctor search by specialty and location via HealthyLinkx
- Brief summary of each recommended doctor's history
- Combined answers that explain the condition and recommend doctors
- Command-line interface
- The agent may proactively recommend a doctor when the question is better answered with a specialist recommendation, but does not always suggest one

### Not included in v1
- Follow-up questions — v1 is strictly single question, single answer
- User accounts or saved preferences
- Appointment booking
- Insurance or cost information

## Success Criteria

- Given symptoms, the agent recommends the right type of specialist
- The agent finds real doctors from the HealthyLinkx directory when relevant
- Each recommended doctor includes a brief background summary
- Answers combine health information with doctor recommendations naturally
- Responses arrive within 15 seconds for simple queries, 30 seconds for doctor searches with background lookups

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

### No follow-up questions
- **Given** a user has already received a response
- **When** the user asks a follow-up question
- **Then** the agent treats it as a new independent question with no conversation history
- **Test**: run two separate invocations — first `"Find me a counselor in Redmond, WA"`, then `"What about orthopedists?"`
- **Verify**: second response does not reference Redmond or counselor — it treats the question as standalone

### Response time
- **Given** any user question
- **When** the agent processes the question
- **Then** the response is returned within 15 seconds for simple queries, 30 seconds for doctor searches with background lookups
- **Test**: simple health question and doctor search, measured with `time docker run ...`
- **Verify**: simple query under 15 seconds, doctor search under 30 seconds

## Examples of Usage

```bash
# Symptom-based question with location
./infra/run.sh "I've been having recurring headaches and blurred vision. I'm in Seattle, WA."

# Find a specific type of doctor
./infra/run.sh "Find me a counselor in Redmond, WA"

# General health question
./infra/run.sh "What's the difference between a cold and the flu?"

# Symptom that warrants specialist care
./infra/run.sh "I've been having sharp chest pains for the past week"

# Search by doctor name and location
./infra/run.sh "Find Dr. Smith in Spokane, WA"

# Multiple symptoms with location
./infra/run.sh "I have knee pain and swelling after running. I live in Bellevue, WA."

# Preventive care question
./infra/run.sh "How often should I get a colonoscopy?"

# Mental health question with location
./infra/run.sh "I've been feeling anxious and can't sleep. I'm in Olympia, WA."
```
