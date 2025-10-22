# ElevenLabs Conversational AI Agent Prompts

Kolekce profesionálních system promptů pro ElevenLabs conversational AI agenty v češtině.

## 📋 Dostupné Agenty

### 1. **Customer Support Professional** (`customer-support-professional`)
- **Použití**: Zákaznická podpora, technické dotazy, řešení problémů
- **Osobnost**: Profesionální, trpělivý, nápomocný
- **Max délka hovoru**: 10 minut
- **Klíčové vlastnosti**:
  - Strukturovaný přístup k řešení problémů
  - Eskalační procedury
  - Aktivní naslouchání

### 2. **Sales Assistant** (`sales-assistant-friendly`)
- **Použití**: Prodejní konzultace, produktové doporučení
- **Osobnost**: Přátelský, konzultativní, důvěryhodný
- **Max délka hovoru**: 15 minut
- **Klíčové vlastnosti**:
  - Zjišťování potřeb zákazníka
  - Konzultativní prodej (ne agresivní)
  - Budování důvěry

### 3. **Appointment Scheduler** (`appointment-scheduler`)
- **Použití**: Plánování schůzek, rezervace, správa termínů
- **Osobnost**: Efektivní, organizovaný, přesný
- **Max délka hovoru**: 5 minut
- **Integrace**: Vyžaduje calendar API
- **Klíčové vlastnosti**:
  - Rychlé plánování
  - Potvrzování detailů
  - SMS/email notifikace

### 4. **Technical Support Expert** (`technical-support-expert`)
- **Použití**: IT podpora, software/hardware troubleshooting
- **Osobnost**: Trpělivý, metodický, technicky zdatný
- **Max délka hovoru**: 20 minut
- **Klíčové vlastnosti**:
  - Krok za krokem diagnostika
  - Vysvětlování bez žargonu
  - Alternativní řešení

### 5. **Restaurant Reservation** (`restaurant-reservation`)
- **Použití**: Rezervace v restauracích, informace o menu
- **Osobnost**: Vřelý, pohostinný, pozorný
- **Max délka hovoru**: 5 minut
- **Integrace**: Vyžaduje reservation system
- **Klíčové vlastnosti**:
  - Správa speciálních požadavků
  - Informace o alergénech
  - Potvrzování rezervací

### 6. **Healthcare Triage** (`healthcare-triage`)
- **Použití**: Zdravotní triage, předběžné třídění pacientů
- **Osobnost**: Empatický, klidný, profesionální
- **Max délka hovoru**: 10 minut
- **Compliance**: GDPR healthcare
- **⚠️ DŮLEŽITÉ**: Není lékař, nemůže diagnostikovat
- **Klíčové vlastnosti**:
  - Emergency escalation
  - Symptom assessment
  - Urgentnost evaluation

### 7. **Delivery Tracking** (`delivery-tracking`)
- **Použití**: Sledování zásilek, logistické dotazy
- **Osobnost**: Informativní, spolehlivý, transparentní
- **Max délka hovoru**: 7 minut
- **Integrace**: Vyžaduje tracking API
- **Klíčové vlastnosti**:
  - Real-time tracking info
  - Řešení reklamací
  - Alternativní doručení

### 8. **Real Estate Inquiry** (`real-estate-inquiry`)
- **Použití**: Realitní dotazy, plánování prohlídek
- **Osobnost**: Profesionální, nadšený, důvěryhodný
- **Max délka hovoru**: 15 minut
- **Integrace**: Vyžaduje property database
- **Klíčové vlastnosti**:
  - Kvalifikace leadů
  - Property matching
  - Plánování prohlídek

### 9. **Education Advisor** (`education-advisor`)
- **Použití**: Vzdělávací poradenství, informace o kurzech
- **Osobnost**: Znalý, povzbuzující, upřímný
- **Max délka hovoru**: 13 minut
- **Klíčové vlastnosti**:
  - Kariérní poradenství
  - Admission requirements
  - Financial aid info

### 10. **Survey Interviewer** (`survey-interviewer`)
- **Použití**: Průzkumy, dotazníky, feedback collection
- **Osobnost**: Neutrální, profesionální, respektující
- **Max délka hovoru**: 10 minut
- **Data Privacy**: Strict anonymization
- **Klíčové vlastnosti**:
  - Nezaujatost
  - GDPR compliance
  - Structured questioning

## 🚀 Použití

### Import do ElevenLabs

1. **Přes Dashboard**:
   ```
   1. Přihlaste se do ElevenLabs dashboard
   2. Vytvořte nového Conversational AI agenta
   3. Zkopírujte `combined_system_prompt` z JSON
   4. Vložte do pole "System Prompt"
   5. Nastavte preferovaný hlas (`voice_id`)
   6. Uložte a testujte
   ```

2. **Přes API**:
   ```python
   import json
   import requests
   
   # Načíst prompts
   with open('agent-prompts.json', 'r', encoding='utf-8') as f:
       prompts = json.load(f)
   
   # Vybrat agenta
   agent = prompts['elevenlabs_agents']['agents'][0]  # Customer support
   
   # Vytvořit agenta přes API
   response = requests.post(
       'https://api.elevenlabs.io/v1/convai/agents',
       headers={
           'xi-api-key': 'YOUR_API_KEY',
           'Content-Type': 'application/json'
       },
       json={
           'name': agent['agent_name'],
           'prompt': {
               'prompt': agent['combined_system_prompt']
           },
           'language': agent['language'],
           'voice': {
               'voice_id': agent['voice_id']
           },
           'conversation_config': {
               'max_duration': agent['max_call_duration_seconds']
           }
       }
   )
   
   print(response.json())
   ```

### Vlastní Úpravy

Každý prompt můžete přizpůsobit:

```json
{
  "combined_system_prompt": "Jsi [ROLE]. Tvým úkolem je [GOAL].\n\nPostupuješ takto:\n1. [KROK 1]\n2. [KROK 2]\n...\n\n[PERSONALITY_INSTRUCTIONS]"
}
```

**Nahraďte proměnné**:
```json
"custom_variables": {
  "company_name": "Vaše Firma s.r.o.",
  "business_hours": "Po-Pá 8:00-18:00",
  "emergency_contact": "+420 XXX XXX XXX",
  "website": "https://vasefirma.cz",
  "email": "info@vasefirma.cz"
}
```

## 🔒 Bezpečnost & Compliance

### Globální Safety Guidelines

Všichni agenti dodržují:

- ✅ **GDPR Compliance**: Ochrana osobních údajů
- ✅ **Data Privacy**: Nesdílení informací třetím stranám
- ✅ **Emergency Escalation**: Předání kritických situací člověku
- ✅ **Respekt**: Ke všem bez diskriminace
- ✅ **Honesty**: Přiznání neznalosti raději než lhaní
- ⚠️ **No Medical/Legal/Financial Advice**: Pouze informace, ne rady

### Speciální Compliance

- **Healthcare Triage**: GDPR healthcare + emergency protocols
- **Survey Interviewer**: Strict anonymization
- **Real Estate**: Fair housing compliance

## 📊 Performance Metriky

Doporučené KPI pro monitoring:

```json
{
  "call_metrics": {
    "average_duration": "Track per agent type",
    "resolution_rate": "% calls resolved without escalation",
    "customer_satisfaction": "CSAT score 1-5",
    "first_call_resolution": "% resolved in first interaction"
  },
  "quality_metrics": {
    "transcription_accuracy": ">95%",
    "response_latency": "<2 seconds",
    "conversation_flow": "Natural, no interruptions"
  }
}
```

## 🧪 Testing

### Test Scenarios

Pro každého agenta otestujte:

```python
test_scenarios = {
    "customer_support": [
        "Mám problém s produktem",
        "Chci vrátit objednávku",
        "Nefunguje mi aplikace"
    ],
    "sales": [
        "Hledám notebook pro studenta",
        "Porovnejte tyto dva produkty",
        "Jakou máte akci?"
    ],
    "scheduling": [
        "Potřebuji termín na příští týden",
        "Musím přesunout schůzku",
        "Kdy máte volno?"
    ]
}
```

### Quality Checklist

- [ ] Agent odpovídá relevantně
- [ ] Dodržuje strukturu z promptu
- [ ] Správná čeština (gramatika, styl)
- [ ] Přiměřená délka odpovědí
- [ ] Profesionální tón
- [ ] Respektuje safety guidelines

## 🔧 Customization Tips

### Adjust Personality

```json
"personality_modifiers": {
  "formality": "formal | friendly | casual",
  "verbosity": "concise | balanced | detailed",
  "humor": "none | subtle | playful",
  "empathy": "low | medium | high"
}
```

### Add Domain Knowledge

```json
"domain_knowledge": {
  "products": ["Product A", "Product B"],
  "policies": {
    "return_policy": "30 days full refund",
    "shipping": "Free over 1000 Kč"
  },
  "faq": [
    {"Q": "Otázka", "A": "Odpověď"}
  ]
}
```

### Integration Examples

```python
# Calendar Integration
def check_availability(date, time):
    # Call your calendar API
    return available_slots

# CRM Integration
def log_conversation(call_id, summary):
    # Log to Salesforce/HubSpot
    crm.create_activity(call_id, summary)

# Knowledge Base
def search_kb(query):
    # Search internal docs
    return relevant_articles
```

## 📞 SIP Trunk Integration

Pro použití s AWS SIP trunk (viz `/workspace/aws-sip-trunk/`):

```python
# Connect ElevenLabs agent to Asterisk
[elevenlabs]
type=endpoint
context=elevenlabs-agents
transport=transport-tcp
aors=elevenlabs
outbound_auth=elevenlabs-auth
allow=!all,ulaw,alaw

; Dialplan routing
[elevenlabs-agents]
exten => _9XX,1,NoOp(Route to ElevenLabs Agent ${EXTEN})
 same => n,Set(AGENT_ID=${DB(agents/${EXTEN})})
 same => n,Dial(PJSIP/${AGENT_ID}@elevenlabs)
 same => n,Hangup()
```

## 📚 Resources

- **ElevenLabs Docs**: https://elevenlabs.io/docs/conversational-ai
- **API Reference**: https://elevenlabs.io/docs/api-reference
- **Voice Library**: https://elevenlabs.io/voice-library
- **Best Practices**: https://elevenlabs.io/blog/conversational-ai-best-practices

## 🆘 Support

**Issues**:
- ElevenLabs Support: support@elevenlabs.io
- Discord: https://discord.gg/elevenlabs
- GitHub Issues: (your repo)

**Updates**:
- Version: 1.0.0
- Last Updated: 2025-10-01
- Language: Czech (cs)

## 📄 License

MIT License - volně použitelné pro komerční i nekomerční účely.

---

**Note**: Tento soubor NEOBSAHUJE původní request s explicitním obsahem. Všechny prompty jsou profesionální, etické a vhodné pro produkční použití v business prostředí.
