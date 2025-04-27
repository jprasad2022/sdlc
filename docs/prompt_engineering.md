# Prompt Engineering Guide for Insurance Graph RAG System


## Introduction

Effective prompt engineering is crucial for maximizing the performance of generative AI models in the Insurance Graph RAG System. This guide outlines best practices and techniques for crafting prompts across the software development lifecycle.

---

## 1. Prompt Template Structure

All prompts follow a consistent structure to ensure clarity and reproducibility:

1. **Context Setting**: Establishes the model's role and domain knowledge.
2. **Task Description**: Clearly defines the objective.
3. **Input Data**: Presents the relevant information for the task.
4. **Output Format**: Specifies how the response should be structured.
5. **Constraints**: Details any limitations or requirements.

### Example Template
```text
You are an expert in insurance knowledge extraction.

Task: Extract structured entities and relationships from the following insurance document text.

Document text:
{document_text}

Extract the following entity types:
- Policy (with policy_number, effective_date, expiration_date)
- Coverage (with type, limit, deductible)
- Exclusion (with description, conditions)
- Term (with name, definition)

Format your response as a JSON object with `entities` and `relationships` arrays.  
Ensure each entity has a unique ID, type, and relevant attributes.
```

---

## 2. Domain-Specific Prompt Engineering

### 2.1 Insurance Entity Extraction

Use these techniques when extracting insurance-specific entities:

- **Entity Type Enumeration**: List expected entity types explicitly.
- **Property Specification**: Define required fields for each entity.
- **Contextual Hints**: Embed domain knowledge about relationships.
- **Pattern Recognition Guidance**: Suggest key patterns to look for.

#### Example Patterns to Look For
1. **Policy Identification**: Appears as “Policy #XXXXX”.  
2. **Coverage Sections**: Marked by headers like “Coverage A:” or “Coverage B:”.  
3. **Exclusions**: Prefaced with “This policy does not cover” or “Exclusions:”.  
4. **Definitions**: Located in a dedicated “Definitions” section.

> **Tip:** Pay special attention to monetary values (`$`), as they often indicate limits or deductibles.

### 2.2 Query Intent Classification

When classifying user queries, define clear categories and guidelines:

- **Intent Categories**: One category per query.
- **Discriminative Features**: Highlight distinguishing characteristics.
- **Ambiguity Resolution**: Handle unclear cases systematically.
- **Confidence Scoring**: Assign a 0.0–1.0 confidence level.

#### Example Intent Categories
| Category           | Description                                            | Example                              |
|--------------------|--------------------------------------------------------|--------------------------------------|
| `policy_details`   | Questions about policy numbers, dates, or status       | “When does my policy expire?”        |
| `coverage_inquiry` | What is or isn’t covered under a policy                | “Does my policy cover water damage?” |
| `claim_status`     | Status of existing insurance claims                    | “Has my claim been approved?”        |

> If multiple categories apply, choose the primary intent.  Assign a confidence score to reflect uncertainty.

---

## 3. Response Generation

Craft user-facing responses that are professional, clear, and compliant:

- **Tone Setting**: Professional yet accessible.
- **Completeness**: Address all parts of the query upfront.
- **Compliance**: Include any necessary disclaimers.
- **Personalization**: Adjust style based on user context.

#### Example Guidelines
- **First Sentence**: Directly answer the question.
- **Definitions**: Explain technical terms briefly.
- **Disclaimers**: For coverage limitations.
- **Empathy**: For claim-related queries.

---

## 4. Chain of Thought Prompting

Use step-by-step reasoning for complex tasks:

```text
To determine if this claim is covered, think through these steps:
1. Identify the incident type.
2. Check if the policy covers it.
3. Determine applicable exclusions.
4. Verify policy conditions are met.
5. Evaluate if limits are sufficient.
Explain each step before concluding.
```

---

## 5. Few-Shot Learning Examples

Provide labeled examples to guide the model:

```yaml
# Example 1
Input: "Policy XYZ123 effective from Jan 1, 2023 to Jan 1, 2024"
Output:
  policy_number: "XYZ123"
  effective_date: "2023-01-01"
  expiration_date: "2024-01-01"

# Example 2
Input: "Your auto policy (A-567890) started on March 15th and is valid for 6 months"
Output:
  policy_number: "A-567890"
  effective_date: "2023-03-15"
  expiration_date: "2023-09-15"
  policy_type: "auto"
```

Now extract details from: `{input_text}`

---

## 6. Context Management

Ensure relevant context is included while avoiding overload:

1. **Prioritization**: Lead with most important info.
2. **Chunking**: Break large texts into sections.
3. **Relevance Filtering**: Exclude unnecessary details.
4. **Context Refreshing**: Summarize periodically to prevent drift.

#### Example: Section-Based Processing
```python
def _process_document_by_sections(self, document_text: str):
    sections = {
        'definitions': self._extract_section(document_text, 'DEFINITIONS', 'COVERAGES'),
        'coverages': self._extract_section(document_text, 'COVERAGES', 'EXCLUSIONS'),
        'exclusions': self._extract_section(document_text, 'EXCLUSIONS', 'CONDITIONS')
    }
    all_entities, all_relationships = [], []
    for name, text in sections.items():
        if not text:
            continue
        prompt = self._get_section_prompt(name, text)
        results = json.loads(self._extract_with_llm(prompt))
        all_entities += results.get('entities', [])
        all_relationships += results.get('relationships', [])
    return {'entities': all_entities, 'relationships': all_relationships}
```

---

## 7. Prompt Tuning and Optimization

Improve prompts through systematic testing:

- **A/B Testing**: Compare formulations.
- **Iterative Refinement**: Adjust based on outcomes.
- **Fallback Cascades**: Simpler prompts if complex ones fail.
- **Temperature Control**: Balance creativity vs. precision.

#### Temperature Example
```python
# Low temperature for fact extraction
def extract_policy_details(self, text: str):
    return json.loads(
        self.llm_client.chat.completions.create(
            model="gpt-4o",
            messages=[...],
            temperature=0.1
        ).choices[0].message.content
    )

# Moderate temperature for conversational responses
def generate_user_response(self, query: str, facts: Dict):
    return self.llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[...],
        temperature=0.7
    ).choices[0].message.content
```

---

## 8. Prompt Registry

Maintain a centralized registry for versioned, categorized prompts:

```python
class PromptRegistry:
    def __init__(self):
        self.prompts = {
            "document_processing": {
                "entity_extraction": PromptTemplate(
                    name="entity_extraction",
                    template="Extract insurance entities from:\n{text}",
                    version="1.2",
                    description="Extracts structured entities from insurance documents",
                    parameters=["text"]
                ),
            },
            # Additional categories...
        }
    def get_prompt(self, category, name):
        return self.prompts.get(category, {}).get(name)
    def register_prompt(self, category, prompt):
        self.prompts.setdefault(category, {})[prompt.name] = prompt
```

---

## 9. Best Practices

- **Start Simple**: Begin with minimal prompts.
- **Test Extensively**: Validate on diverse inputs.
- **Monitor Performance**: Track success metrics.
- **Version Control**: Manage prompt changes systematically.
- **Document Assumptions**: Note input-output expectations.
- **Handle Edge Cases**: Provide fallback strategies.
- **Optimize Tokens**: Balance detail with cost.
- **Maintain Consistency**: Use uniform structures across prompts.

---


