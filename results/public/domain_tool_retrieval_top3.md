# DomainToolBench Top-3 Embedding Retrieval

- Embedding model: `mxbai-embed-large` through Ollama
- Full catalog size: 13
- Retrieved tools per task: 3
- Tasks with expected tools: 11
- Mean expected-tool recall: 95.5%
- Perfect-recall tasks: 10/11

| Task | Expected tools | Selected tools | Recall |
|---|---|---|---:|
| `lca-discovery-001` | search_entities | search_entities;create_product_system;check_mass_balance | 100.0% |
| `lca-method-001` | search_entities | get_impact_result;calculate_impacts;search_entities | 100.0% |
| `lca-calc-001` | calculate_impacts | calculate_impacts;get_impact_result;get_contributions | 100.0% |
| `lca-calc-missing-001` | none | calculate_impacts;get_contributions;get_impact_result | n/a |
| `lca-contribution-001` | get_contributions | get_contributions;get_impact_result;search_entities | 100.0% |
| `lca-abstain-001` | none | get_tea_result;check_mass_balance;get_impact_result | n/a |
| `tea-run-001` | run_tea_scenario | run_tea_scenario;get_tea_result;set_tea_parameter | 100.0% |
| `tea-unit-001` | set_tea_parameter | set_tea_parameter;get_tea_result;run_tea_scenario | 100.0% |
| `tea-invalid-001` | none | run_tea_scenario;get_tea_result;set_tea_parameter | n/a |
| `tea-sequence-001` | compare_tea_scenarios;run_tea_scenario | get_tea_result;run_tea_scenario;set_tea_parameter | 50.0% |
| `bioflow-feed-001` | set_stream_composition | set_stream_composition;check_mass_balance;set_tea_parameter | 100.0% |
| `bioflow-run-001` | run_flowsheet | run_flowsheet;check_mass_balance;get_tea_result | 100.0% |
| `bioflow-sequence-001` | check_mass_balance;run_flowsheet | check_mass_balance;run_flowsheet;get_tea_result | 100.0% |
| `bioflow-abstain-001` | none | get_tea_result;create_product_system;run_tea_scenario | n/a |
| `cross-domain-router-001` | get_impact_result;get_tea_result | get_tea_result;get_impact_result;get_contributions | 100.0% |

Retrieval is automatic and does not use the expected tool labels when selecting tools.
The benchmark remains provisional and small.
