# SolarIQ — Week 4: Evaluation and Reliability



## Objective



Improve the reliability, explainability, and measurable quality of SolarIQ's AI-generated solar assessments through repeatable evaluation scenarios, response checks, and automated tests.



## Starting Point



Reuse the Week 3 SolarIQ agent, tools, schemas, and safety controls.



## Implementation



1\. Created a repeatable evaluation dataset covering expected agent behaviours.

2\. Added response checks for evidence grounding and unsupported claims.

3\. Added checks for cautious assessment when plant telemetry is unavailable.

4\. Evaluated root-cause hypotheses and recommendation risk classification.

5\. Added automated tests for evaluation criteria and failure cases.

6\. Generated an evaluation report from repeatable evaluation scenarios.

7\. Established a foundation for exploring LLM-as-a-Judge and Evidently AI in future iterations.



## Safety Principles



\- Do not invent plant measurements or telemetry.

\- Distinguish observed evidence, estimates, and documented knowledge.

\- Do not confirm underperformance without suitable measured data.

\- Require human approval for high- or critical-risk recommendations.

\- Never directly control physical equipment.



## Validation



### Automated Tests



Run the Week 3 agent and Week 4 evaluation tests from the repository root:



```bash

python -m pytest week3-agent/tests week4-evaluation/tests -q

```



**Latest validation result:** 33 tests passed.



### Evaluation Scenarios



The evaluation run completed six scenarios with 18 of 18 checks passing, achieving a 100% check-pass rate for that run.



Report: `week4-evaluation/evaluation_report.json`



These results demonstrate that the implemented checks passed for the tested scenarios. They do not establish universal correctness or production readiness.



## Status



**Implementation and initial validation completed.**



Automated tests and repeatable evaluation scenarios are available. Further work should focus on broader scenario coverage, live API failure handling, evaluation of real-world outputs, and assessing whether LLM-as-a-Judge and Evidently AI add value.

