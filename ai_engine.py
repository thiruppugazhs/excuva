import os
import json
import random
import re
from datetime import datetime, timedelta

# Attempt to configure Gemini if available
gemini_available = False
try:
    import google.generativeai as genai
    gemini_available = True
except ImportError:
    pass

RECIPIENT_PROFILES = {
    'Professor': {'salutation': 'Dear Professor {recipient_name},', 'signoff': 'Thank you for your consideration,\n{user_name}'},
    'Teacher': {'salutation': 'Dear Mr./Ms. {recipient_name},', 'signoff': 'Best regards,\n{user_name}'},
    'Manager': {'salutation': 'Hi {recipient_name},', 'signoff': 'Best regards,\n{user_name}'},
    'Employer': {'salutation': 'Dear {recipient_name},', 'signoff': 'Sincerely,\n{user_name}'},
    'Client': {'salutation': 'Hi {recipient_name},', 'signoff': 'Warm regards,\n{user_name}'},
    'Friend': {'salutation': 'Hey {recipient_name},', 'signoff': 'Talk soon,\n{user_name}'},
    'Parent': {'salutation': 'Hey Mom / Dad,', 'signoff': 'Love,\n{user_name}'},
    'Colleague': {'salutation': 'Hey {recipient_name},', 'signoff': 'Thanks,\n{user_name}'},
    'Other': {'salutation': 'Hello {recipient_name},', 'signoff': 'Regards,\n{user_name}'}
}

LENGTH_GUIDELINES = {
    'Very Short': '1 concise sentence, maximum 25 words. Straight to the point with zero filler.',
    'Short': '2-3 sentences, around 40-60 words. Clear reason and immediate next step.',
    'Medium': '1-2 well-crafted paragraphs, around 80-120 words. Complete explanation with context and polite resolution.',
    'Detailed': '2-3 thorough paragraphs, around 150-220 words. Comprehensive context, clear timeline, sincere acknowledgment, and proactive next steps.'
}

DELIVERY_FORMATS = {
    'WhatsApp': 'Casual and natural mobile chat format. Crisp spacing, modern conversational tone.',
    'Email': 'Professional email format with a clear Subject line at top (e.g., "Subject: ..."), formal greeting, structured body paragraphs, and professional closing with sender name.',
    'SMS': 'Concise text message format with no email fluff. Direct, polite, and immediate.',
    'In Person': 'Spoken dialogue script. Phrases written naturally as if being spoken aloud face-to-face (e.g., "I wanted to come talk to you directly...").',
    'College Portal': 'Academic student submission format with student context, course reference placeholder, and formal academic etiquette.',
    'Work Chat': 'Slack/Teams style message. Clear, collaborative, workplace-appropriate, with direct action items.',
    'Other': 'Clean, versatile standard text message.'
}

def clean_llm_json(text):
    text = text.strip()
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        text = match.group(1)
    try:
        return json.loads(text)
    except Exception:
        return None

def generate_excuse_with_gemini(api_key, scenario, recipient, situation_type="General", tone="Professional", length="Medium", delivery_method="Email", user_name="Alex", details=""):
    if not gemini_available or not api_key:
        return None
    
    candidate_models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-pro"]
    
    prompt = f"""
You are an expert communications specialist crafting realistic, believable, and context-tailored explanations.

Input Parameters:
- Situation Description: {scenario}
- Situation Category: {situation_type}
- Intended Recipient: {recipient}
- Selected Tone: {tone}
- Desired Length: {length} ({LENGTH_GUIDELINES.get(length, 'Medium length')})
- Delivery Channel: {delivery_method} ({DELIVERY_FORMATS.get(delivery_method, 'Standard format')})
- Sender Name: {user_name}
- Additional Constraints: {details if details else 'None'}

Formatting Rules:
1. If Delivery Channel is 'Email', start the text with "Subject: [Clear, Professional Subject Line]" followed by a blank line, salutation, body, and closing.
2. If Delivery Channel is 'In Person', phrase it as a spoken conversational script that sounds natural when spoken aloud.
3. If Delivery Channel is 'WhatsApp' or 'SMS', keep it conversational without email subjects.
4. Adhere strictly to the requested length ({length}).
5. Generate a primary response plus 2 diverse alternative variants, an estimated believability score (85-99), risk level (Low, Moderate), and 3 actionable tactical follow-up tips.

Return ONLY a JSON object matching this schema:
{{
  "primary_text": "Full drafted message ready to send or speak",
  "variations": [
    {{"title": "Concise Option", "text": "Short alternative"}},
    {{"title": "Detailed Option", "text": "Detailed alternative"}}
  ],
  "believability_score": 96,
  "risk_level": "Low",
  "tips": [
    "Send the explanation at least 15 minutes before the scheduled time.",
    "Proactively propose a specific rescheduling window.",
    "Keep your explanation consistent if asked for minor clarification."
  ]
}}
"""
    for model_name in candidate_models:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            parsed = clean_llm_json(response.text)
            if parsed and 'primary_text' in parsed:
                return parsed
        except Exception as e:
            continue
    return None

def generate_excuse_contextual(scenario, recipient, situation_type="Missed deadline", tone="Professional", length="Medium", delivery_method="Email", user_name="Alex", details=""):
    rec_info = RECIPIENT_PROFILES.get(recipient, {'salutation': f'Hi {recipient},', 'signoff': f'Best regards,\n{user_name}'})
    salutation = rec_info['salutation'].format(recipient_name=recipient, user_name=user_name)
    signoff = rec_info['signoff'].format(recipient_name=recipient, user_name=user_name)
    
    scenario_lower = scenario.lower()
    sit_type_lower = situation_type.lower()
    
    is_assignment = 'deadline' in sit_type_lower or 'assignment' in scenario_lower or 'submission' in scenario_lower or 'homework' in scenario_lower
    is_late = 'late' in sit_type_lower or 'running late' in scenario_lower or 'traffic' in scenario_lower
    is_meeting = 'meeting' in sit_type_lower or 'call' in scenario_lower or 'appointment' in scenario_lower
    
    if is_assignment:
        subject = f"Subject: Request for Late Submission / Assignment Update — {user_name}"
    elif is_late:
        subject = f"Subject: Running Late / Schedule Update — {user_name}"
    elif is_meeting:
        subject = f"Subject: Rescheduling Today's Meeting — {user_name}"
    else:
        subject = f"Subject: Urgent Schedule Update & Sincere Apologies — {user_name}"

    if length == 'Very Short':
        if delivery_method == 'In Person':
            primary_body = f"I'm really sorry, but an unexpected personal emergency came up this morning that I had to attend to immediately."
            var1 = f"My apologies for the delay—I ran into an unforeseen issue on my way here, but I'm ready to get started now."
            var2 = f"I wanted to apologize directly for missing our deadline. I experienced a sudden conflict but have everything completed now."
        elif delivery_method == 'SMS' or delivery_method == 'WhatsApp':
            primary_body = f"Hi {recipient}, so sorry but an unexpected personal issue came up today. I'm taking care of it now and will follow up shortly!"
            var1 = f"Hey {recipient}, apologies for the short notice—running into an unavoidable delay today. Will update you in 30 mins."
            var2 = f"Hi {recipient}, really sorry about the delay. I had a sudden emergency this morning but will be back on track this afternoon."
        elif delivery_method == 'Email':
            primary_body = f"{subject}\n\n{salutation}\n\nPlease accept my sincere apologies for the delay due to an unexpected personal emergency today. I am following up shortly with the completed materials.\n\n{signoff}"
            var1 = f"{subject}\n\n{salutation}\n\nI am writing to apologize for my delay today due to unforeseen urgent circumstances. I will provide a full update this afternoon.\n\n{signoff}"
            var2 = f"{subject}\n\n{salutation}\n\nDue to an unexpected conflict this morning, I will be delayed. I appreciate your patience and will reconnect shortly.\n\n{signoff}"
        else:
            primary_body = f"Hi {recipient}, my apologies for the delay. An unexpected personal issue arose this morning, but I am resolving it now and will update you shortly."
            var1 = f"Apologies for the delay today—handled an urgent conflict and will have everything submitted shortly."
            var2 = f"Hi {recipient}, stepped away due to a sudden situation this morning. Back online shortly."

    elif length == 'Short':
        if delivery_method == 'In Person':
            primary_body = f"I wanted to come talk to you directly to apologize. An unexpected personal issue developed this morning that prevented me from finishing on time. I have it ready now and would really appreciate your understanding."
            var1 = f"I'm very sorry about the delay today. I was held up by an unforeseen transit and mechanical issue on my commute, but I'm here now to catch up on everything."
            var2 = f"I apologize sincerely for the scheduling conflict. Something urgent came up on my end, but I've cleared my schedule for the rest of the day."
        elif delivery_method == 'SMS' or delivery_method == 'WhatsApp':
            primary_body = f"Hi {recipient}, I wanted to apologize for the delay regarding {scenario}. I ran into an unexpected personal issue early today, but I'm wrapping things up now and will send everything over shortly!"
            var1 = f"Hey {recipient}, so sorry for the delay on {scenario}. Dealt with an unexpected situation this morning. Sending over the completed work very soon!"
            var2 = f"Hi {recipient}, my sincere apologies for the short notice. Unforeseen circumstances held me up, but I will be fully available in about an hour."
        elif delivery_method == 'Email':
            primary_body = f"{subject}\n\n{salutation}\n\nI am writing to sincerely apologize for the delay regarding {scenario}. An unexpected personal matter arose early this morning that required my immediate attention.\n\nI have now addressed the issue and am finalizing the remaining details. I will deliver the completed work by this afternoon.\n\n{signoff}"
            var1 = f"{subject}\n\n{salutation}\n\nI apologize for missing our scheduled timeline today due to an unavoidable conflict. I am actively working on resolving this and will follow up shortly.\n\n{signoff}"
            var2 = f"{subject}\n\n{salutation}\n\nDue to unexpected logistical challenges this morning, I was unable to submit {scenario} on time. Thank you for your patience while I finalize the deliverable.\n\n{signoff}"
        else:
            primary_body = f"Hi {recipient}, I apologize for the delay regarding {scenario}. An unexpected situation developed this morning, but I'm finalizing everything now and will submit shortly."
            var1 = f"Hi {recipient}, brief update: delayed this morning due to an urgent personal conflict. Wrapping up the work right now."
            var2 = f"My apologies for the delay on {scenario}. Resolving the final details and will submit within the hour."

    elif length == 'Detailed':
        if delivery_method == 'In Person':
            primary_body = f"I wanted to speak with you directly to apologize for the delay regarding {scenario}. Early this morning, I was confronted with an unexpected and unavoidable personal issue that required my full attention for several hours.\n\nI take full responsibility for not being able to communicate sooner. I have since worked through the matter and have completed all the required components. I would be extremely grateful for the opportunity to submit the work and discuss any questions you might have."
            var1 = f"I wanted to apologize face-to-face for my delay. I encountered an unforeseen emergency on my commute that caused major disruption, but I made sure to complete all pending items as soon as I was able. Thank you for your patience."
            var2 = f"Thank you for taking a moment to speak with me. I experienced a sudden personal emergency this morning that threw off my schedule, but I have resolved it and am ready to hand over the deliverable immediately."
        elif delivery_method == 'Email':
            primary_body = f"{subject}\n\n{salutation}\n\nI am writing to offer my sincere apologies for missing the scheduled timeline for {scenario}. Unfortunately, an unexpected personal emergency arose early this morning which required my immediate and undivided attention, preventing me from submitting on time.\n\nI understand the importance of this commitment and truly regret any inconvenience or disruption this may have caused to your schedule. I have now resolved the situation and completed the work thoroughly to ensure it meets our quality standards.\n\nAttached is the completed deliverable. I would greatly appreciate your understanding and would be glad to discuss any questions at your convenience.\n\n{signoff}"
            var1 = f"{subject}\n\n{salutation}\n\nI am reaching out to provide a transparent explanation regarding my delay with {scenario}. Due to unexpected circumstances beyond my control this morning, I was temporarily delayed. All core requirements are now completed and verified.\n\nThank you for your accommodation and understanding.\n\n{signoff}"
            var2 = f"{subject}\n\n{salutation}\n\nI am writing to respectfully request your consideration regarding {scenario}. An unexpected matter developed today which delayed my progress. I have now finalized the entire submission and look forward to your feedback.\n\n{signoff}"
        else:
            primary_body = f"Hi {recipient}, I wanted to reach out with my sincere apologies regarding the delay on {scenario}.\n\nAn unexpected personal matter arose early this morning that required my immediate attention. I understand this causes an inconvenience and I take full accountability. I have now resolved the issue and finalized the complete work.\n\nI am submitting everything now. Thank you so much for your patience and understanding!"
            var1 = f"Hi {recipient}, apologies for the delay today. An urgent conflict came up this morning, but I've resolved it and finished all pending items. Sending the details over now."
            var2 = f"Hi {recipient}, so sorry for missing the planned schedule for {scenario}. Dealt with an unexpected situation earlier today, but everything is polished and ready."

    else: # Medium (Default)
        if delivery_method == 'In Person':
            primary_body = f"I apologize for the delay regarding {scenario}. I encountered an unexpected personal issue early this morning that affected my schedule. I have now completed everything and would appreciate the opportunity to submit it."
            var1 = f"I'm very sorry about the delay today. An unavoidable issue came up this morning, but I've resolved it and am ready with the full update."
            var2 = f"I wanted to apologize directly for missing our timeline. I had an urgent conflict earlier, but I've finished the work and would love to hand it in."
        elif delivery_method == 'SMS' or delivery_method == 'WhatsApp':
            primary_body = f"Hi {recipient}, I apologize for missing the deadline for {scenario}. I encountered an unexpected personal issue early today that affected my schedule. I've now completed the work and would appreciate the opportunity to submit it!"
            var1 = f"Hey {recipient}, so sorry for the delay on {scenario}. Ran into an unforeseen issue earlier today, but I'm wrapping it up and sending it over right now."
            var2 = f"Hi {recipient}, sincere apologies for the delay. An unexpected conflict came up this morning, but I have everything ready for you now."
        elif delivery_method == 'Email':
            primary_body = f"{subject}\n\n{salutation}\n\nI apologize for missing the deadline for {scenario}. I encountered an unexpected personal issue early today that affected my ability to complete the work on time.\n\nI have now completed everything and would appreciate the opportunity to submit it. Thank you for your time and understanding.\n\n{signoff}"
            var1 = f"{subject}\n\n{salutation}\n\nI am writing to apologize for the delay regarding {scenario}. Due to unforeseen circumstances this morning, I was temporarily held up. I have finalized the submission and appreciate your flexibility.\n\n{signoff}"
            var2 = f"{subject}\n\n{salutation}\n\nDue to an urgent matter that developed early today, I was delayed with {scenario}. All components are now prepared and ready for your review.\n\n{signoff}"
        else:
            primary_body = f"Hi {recipient}, I apologize for missing the scheduled timeline for {scenario}. I encountered an unexpected issue this morning, but I have now completed the work and would appreciate the opportunity to submit it."
            var1 = f"Apologies for the delay on {scenario} today. An unforeseen conflict arose this morning, but I'm submitting the completed deliverable now."
            var2 = f"Hi {recipient}, sorry for the delay. Ran into an unexpected issue earlier, but everything is finalized and ready."

    var1_text = var1 if 'var1' in locals() else primary_body
    var2_text = var2 if 'var2' in locals() else primary_body

    return {
        'primary_text': primary_body,
        'variations': [
            {'title': 'Direct & Concise', 'text': var1_text},
            {'title': 'Context-Rich & Detailed', 'text': var2_text}
        ],
        'believability_score': random.randint(94, 98),
        'risk_level': 'Low',
        'tips': [
            f"Send via {delivery_method} as soon as possible to demonstrate reliability.",
            "Keep your explanation consistent if asked for minor clarification.",
            "Follow up with confirmation once the submission or arrival is complete."
        ]
    }

def rewrite_excuse_with_gemini(api_key, original_text, instruction, tone="Professional", user_name="Alex"):
    if not gemini_available or not api_key:
        return None
    candidate_models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-pro"]
    prompt = f"""
You are a professional communications specialist.
Rewrite the following message according to the user's specific instruction.

Original Message:
\"\"\"{original_text}\"\"\"

Instruction / Goal:
{instruction}

Target Tone:
{tone}

Sender Name:
{user_name}

Rules:
- Keep the message authentic, natural, believable, and ready to send.
- No conversational filler, no robot tags. Return ONLY the rewritten message text.
"""
    for model_name in candidate_models:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text:
                return text
        except Exception:
            continue
    return None

def rewrite_excuse_contextual(original_text, instruction, user_name="Alex"):
    """
    Contextual rewriting engine for quick modifications:
    - Make Shorter
    - Make More Formal
    - Make More Casual
    - Make Friendlier
    - Make More Natural
    - Make Apologetic
    - Custom prompts
    """
    inst_lower = instruction.lower()
    lines = original_text.strip().split('\n')
    
    # Extract existing subject/greeting if present
    subject_line = ""
    greeting_line = ""
    body_lines = []
    
    for l in lines:
        if l.startswith("Subject:"):
            subject_line = l
        elif any(l.startswith(w) for w in ['Dear', 'Hi', 'Hey', 'Hello']) and not greeting_line:
            greeting_line = l
        elif not any(l.startswith(w) for w in ['Sincerely', 'Best regards', 'Warm regards', 'Thanks', 'Regards', 'Love']):
            body_lines.append(l)

    header = f"{subject_line}\n\n{greeting_line}".strip() if (subject_line or greeting_line) else ""
    if not header:
        header = f"Hi,\n"

    if 'short' in inst_lower or 'concise' in inst_lower or 'brief' in inst_lower:
        return f"{header}\n\nDue to an urgent personal conflict that arose this morning, I will be delayed today. I apologize for the inconvenience and will follow up shortly.\n\nBest regards,\n{user_name}"
    
    if 'formal' in inst_lower or 'official' in inst_lower or 'corporate' in inst_lower:
        return f"{header}\n\nI am writing to formally communicate an unavoidable circumstance that precludes my scheduled participation today. Every measure is being taken to minimize disruption, and I will submit all required deliverables at the earliest opportunity.\n\nThank you for your understanding.\n\nSincerely,\n{user_name}"

    if 'casual' in inst_lower or 'informal' in inst_lower or 'relaxed' in inst_lower:
        return f"Hey,\n\nSo sorry for the delay! Something unexpected came up on my end this morning that I had to take care of. Getting back to work now and will send everything over soon.\n\nTalk soon,\n{user_name}"

    if 'friend' in inst_lower or 'warm' in inst_lower:
        return f"{header}\n\nI wanted to reach out and apologize for the delay today! I ran into an unexpected situation this morning, but I'm wrapping everything up right now and will update you shortly. Really appreciate your patience!\n\nWarmly,\n{user_name}"

    if 'natural' in inst_lower or 'human' in inst_lower or 'spoken' in inst_lower:
        return f"{header}\n\nI'm really sorry about this, but I ran into an unexpected personal issue earlier today that threw off my schedule. I've got everything sorted now and am finishing up the rest. Thanks so much for bearing with me!\n\nBest,\n{user_name}"

    if 'apologetic' in inst_lower or 'sorry' in inst_lower or 'sincere' in inst_lower:
        return f"{header}\n\nI want to offer my deepest and most sincere apologies for the delay today. I understand this causes an inconvenience to your schedule, and I take full accountability. I am finalizing the deliverable right now to make this right.\n\nThank you for your gracious understanding.\n\nSincerely,\n{user_name}"

    # General custom modification
    return f"{header}\n\nRegarding our schedule: due to unexpected personal circumstances that developed today, I need to adjust my timeline. I have addressed the issue and am finalizing all required items now.\n\nThank you for your patience.\n\nBest regards,\n{user_name}"

def generate_formal_document_content(doc_type, title, recipient, issue_date, reason, additional_details, user_name):
    """
    Legitimate formal document generator for Part 3:
    Types:
    - Explanation Letter
    - Personal Declaration
    - Leave Request
    - Delay Notification
    - Appointment Request
    - Incident Explanation
    - Extension Request
    - Absence Explanation
    - Other
    """
    date_str = issue_date or datetime.now().strftime('%d %B %Y')
    rec_str = recipient or "Recipient"
    reason_str = reason or "an unexpected personal circumstance"
    
    # Document Type Phrasing
    type_headers = {
        'Extension Request': 'ASSIGNMENT & DEADLINE EXTENSION REQUEST',
        'Explanation Letter': 'FORMAL WRITTEN EXPLANATION LETTER',
        'Personal Declaration': 'PERSONAL DECLARATION OF RECORD',
        'Leave Request': 'FORMAL LEAVE & ABSENCE REQUEST',
        'Delay Notification': 'OFFICIAL SCHEDULE DELAY NOTIFICATION',
        'Appointment Request': 'FORMAL RESCHEDULING & APPOINTMENT REQUEST',
        'Incident Explanation': 'FORMAL STATEMENT OF UNFORESEEN INCIDENT',
        'Absence Explanation': 'NOTICE OF UNAVOIDABLE ABSENCE & EXPLANATION',
        'Other': title.upper() if title else 'FORMAL ADMINISTRATIVE STATEMENT'
    }

    doc_header = type_headers.get(doc_type, title.upper() if title else 'FORMAL ADMINISTRATIVE STATEMENT')
    subject = f"Subject: {title if title else f'Request regarding {doc_type}'}"

    if 'extension' in doc_type.lower():
        body = f"""I am writing to respectfully request an extension for my pending submission due to {reason_str}.

Due to these unforeseen circumstances, I was temporarily unable to complete the required components according to our original timeline. {additional_details if additional_details else 'I have now resolved the matter and am actively finalizing the work.'}

I sincerely apologize for any disruption to your schedule and would be deeply grateful for your consideration in granting additional time to complete and submit this work."""

    elif 'leave' in doc_type.lower() or 'absence' in doc_type.lower():
        body = f"""I am writing to formally notify you of my unavoidable absence on {date_str} due to {reason_str}.

{additional_details if additional_details else 'I have taken necessary measures to ensure all urgent matters are prioritized and will resume full duties immediately upon my return.'}

Thank you for your understanding and consideration regarding this matter."""

    elif 'delay' in doc_type.lower():
        body = f"""I am writing to officially communicate an unexpected delay regarding our schedule on {date_str} caused by {reason_str}.

{additional_details if additional_details else 'I am taking every step to minimize any impact and will follow up immediately with the completed items.'}

I appreciate your patience and flexibility."""

    elif 'incident' in doc_type.lower():
        body = f"""This document serves as a formal written record of the unforeseen incident that occurred on {date_str} involving {reason_str}.

{additional_details if additional_details else 'All relevant parties were notified promptly and appropriate remediation steps have been initiated.'}

I remain available to provide any additional clarification or documentation as required."""

    else:
        body = f"""I am submitting this written statement regarding our scheduled obligations on {date_str}.

This explanation is provided due to {reason_str}. {additional_details if additional_details else 'I have made every effort to minimize inconvenience and look forward to resolving this matter promptly.'}

Thank you for your time, understanding, and continued support."""

    full_formatted_text = f"""{doc_header}

Date: {date_str}

To,
{rec_str}

{subject}

Dear {rec_str},

{body}

Thank you for your consideration.

Sincerely,
{user_name}"""

    return {
        'doc_type': doc_type,
        'title': title or doc_header,
        'recipient': rec_str,
        'issue_date': date_str,
        'reason': reason_str,
        'content_text': full_formatted_text
    }
