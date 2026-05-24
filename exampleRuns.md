## Example Runs

### (1) Query

```
What are the top 5 most commonly used interventions in studies related to diabetes?
```

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the top 5 most commonly used interventions in studies related to diabetes?"
  }' | jq
```

### (1) Answer

```json
{
  "visualization": {
    "type": "bar_chart",
    "title": "List the top 5 most commonly used interventions in clinical studies related to diabetes.",
    "encoding": {
      "x": {
        "field": "category",
        "type": "nominal"
      },
      "y": {
        "field": "trial_count",
        "type": "quantitative"
      }
    },
    "data": [
      {
        "citations": [
          {
            "nct_id": "NCT06660173",
            "excerpt": "A Study of Maridebart Cafraglutide in Adult Participants With Type 2 Diabetes Mellitus (T2DM)"
          },
          {
            "nct_id": "NCT03235050",
            "excerpt": "A Study to Evaluate the Efficacy and Safety of MEDI0382 in the Treatment of Overweight and Obese Subjects With Type 2 Diabetes"
          },
          {
            "nct_id": "NCT02183324",
            "excerpt": "BI 1356 BS in Japanese Patients With Type 2 Diabetes Mellitus"
          },
          {
            "nct_id": "NCT06254274",
            "excerpt": "A Study of RAY1225 in Participants With Type 2 Diabetes"
          },
          {
            "nct_id": "NCT01754259",
            "excerpt": "Effects of Ranolazine on Coronary Flow Reserve in Symptomatic Diabetic Patients and CAD"
          }
        ],
        "category": "Placebo",
        "trial_count": 47
      },
      {
        "citations": [
          {
            "nct_id": "NCT00316082",
            "excerpt": "Study of BMS-477118 as Monotherapy With Titration in Subjects With Type 2 Diabetes Who Are Not Controlled With Diet and Exercise"
          },
          {
            "nct_id": "NCT00316082",
            "excerpt": "Study of BMS-477118 as Monotherapy With Titration in Subjects With Type 2 Diabetes Who Are Not Controlled With Diet and Exercise"
          },
          {
            "nct_id": "NCT00316082",
            "excerpt": "Study of BMS-477118 as Monotherapy With Titration in Subjects With Type 2 Diabetes Who Are Not Controlled With Diet and Exercise"
          },
          {
            "nct_id": "NCT00316082",
            "excerpt": "Study of BMS-477118 as Monotherapy With Titration in Subjects With Type 2 Diabetes Who Are Not Controlled With Diet and Exercise"
          },
          {
            "nct_id": "NCT00950599",
            "excerpt": "Study of Multiple Doses of Saxagliptin (BMS-477118)"
          }
        ],
        "category": "Saxagliptin",
        "trial_count": 10
      },
      {
        "citations": [
          {
            "nct_id": "NCT01725126",
            "excerpt": "To Investigate the Safety, Tolerability and Pharmacodynamics of GSK2890457 in Healthy Volunteers and Subjects With Type 2 Diabetes"
          },
          {
            "nct_id": "NCT03570632",
            "excerpt": "Metformin for Preeclampsia Prevention in Pregnant Women With Type 1 Diabetes Mellitus"
          },
          {
            "nct_id": "NCT07254572",
            "excerpt": "Anti-atherosclerotic Efficacy of Selected Antidiabetic Drugs in Patients With Coronary Artery Disease and Pre-diabetes"
          },
          {
            "nct_id": "NCT02393573",
            "excerpt": "Attenuating The Post-Operative Insulin Resistance And Promoting Protein Anabolism"
          },
          {
            "nct_id": "NCT02202161",
            "excerpt": "A Study Investigating Safety, Tolerability, Pharmacokinetics and Pharmacodynamics of GSK2330672 Administered With Metformin to Type 2 Diabetes Patients"
          }
        ],
        "category": "Metformin",
        "trial_count": 10
      },
      {
        "citations": [
          {
            "nct_id": "NCT01888796",
            "excerpt": "Diastolic Dysfunction in Patients With Type 2 Diabetes Mellitus"
          },
          {
            "nct_id": "NCT00937703",
            "excerpt": "Multicentric Evaluation of Two Telematics Systems in Type 2 Diabetic Patients in Failure of Oral Treatment and Having to Start Treatment by Basal Insulin"
          },
          {
            "nct_id": "NCT02039544",
            "excerpt": "A Study of Xuebi Formula for Diabetic Peripheral Neuropathy(Qi-deficiency and Blood-stasis)"
          },
          {
            "nct_id": "NCT01507272",
            "excerpt": "Safety and Tolerability of Liraglutide in Healthy Male Volunteers"
          },
          {
            "nct_id": "NCT01507272",
            "excerpt": "Safety and Tolerability of Liraglutide in Healthy Male Volunteers"
          }
        ],
        "category": "placebo",
        "trial_count": 9
      },
      {
        "citations": [
          {
            "nct_id": "NCT03235050",
            "excerpt": "A Study to Evaluate the Efficacy and Safety of MEDI0382 in the Treatment of Overweight and Obese Subjects With Type 2 Diabetes"
          },
          {
            "nct_id": "NCT03011008",
            "excerpt": "Liraglutide as Additional Treatment to Insulin in Patients With Autoimmune Diabetes Mellitus"
          },
          {
            "nct_id": "NCT04829903",
            "excerpt": "Dulaglutide Versus Liraglutide in Obese Type 2 Diabetic Adolescents Using Metformin"
          },
          {
            "nct_id": "NCT05162183",
            "excerpt": "Replication of the LEAD-2 Diabetes Trial in Healthcare Claims Data"
          },
          {
            "nct_id": "NCT01725126",
            "excerpt": "To Investigate the Safety, Tolerability and Pharmacodynamics of GSK2890457 in Healthy Volunteers and Subjects With Type 2 Diabetes"
          }
        ],
        "category": "Liraglutide",
        "trial_count": 8
      }
    ]
  },
  "meta": {
    "filters_applied": {
      "condition": "diabetes"
    },
    "source": "ClinicalTrials.gov v2 API",
    "query_interpretation": "List the top 5 most commonly used interventions in clinical studies related to diabetes.",
    "assumptions": [
      "Visualization type determined by rule-based fallback"
    ],
    "trial_count": 500,
    "total_matching": 23841,
    "phase_filter_mode": "inclusive_hybrid"
  }
}
```

---

### (2) Query

```
Which countries conduct the most lung cancer clinical trials?
```

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Which countries conduct the most lung cancer clinical trials?"
  }' | jq
```

### (2) Answer

```json
{
  "visualization": {
    "type": "bar_chart",
    "title": "Identify the countries that conduct the highest number of clinical trials for lung cancer.",
    "encoding": {
      "x": {
        "field": "category",
        "type": "nominal"
      },
      "y": {
        "field": "trial_count",
        "type": "quantitative"
      }
    },
    "data": [
      {
        "citations": [
          {
            "nct_id": "NCT00544596",
            "excerpt": "R-(-)-Gossypol Acetic Acid, Cisplatin, and Etoposide in Treating Patients With Advanced Solid Tumors or Extensive Stage Small Cell Lung Cancer"
          },
          {
            "nct_id": "NCT01061788",
            "excerpt": "A Trial of AMG 479, Everolimus (RAD001) and Panitumumab in Patients With Advanced Cancer - QUILT-3.007"
          },
          {
            "nct_id": "NCT01994382",
            "excerpt": "Phase 1/2a Dose Escalation Study in Participants With CLL, SLL, or NHL"
          },
          {
            "nct_id": "NCT06549088",
            "excerpt": "Analysis of Lung Cancer Tissue With Spatial Frequency Domain Imaging"
          },
          {
            "nct_id": "NCT06451003",
            "excerpt": "Intervention to Improve Utilization of Extended Venous Thromboembolism Prophylaxis After Cancer Surgery"
          }
        ],
        "category": "United States",
        "trial_count": 165
      },
      {
        "citations": [
          {
            "nct_id": "NCT05693246",
            "excerpt": "Effect of Perioperative Use of Glycopyrrolate on Lung Function in Patients Under General Anesthesia"
          },
          {
            "nct_id": "NCT06123754",
            "excerpt": "Phase III Study of Envafolimab Versus Placebo Plus Chemotherapy in Resectable Stage III NSCLC"
          },
          {
            "nct_id": "NCT06127303",
            "excerpt": "Toripalimab Combined With Cryoablation for First-line Oligo-progression in Driver-negative Advanced NSCLC"
          },
          {
            "nct_id": "NCT02040870",
            "excerpt": "LDK378 in Adult Chinese Patients With ALK-rearranged (ALK-positive) Advanced Non-small Cell Lung Cancer (NSCLC) Previously Treated With Crizotinib"
          },
          {
            "nct_id": "NCT06338683",
            "excerpt": "Survival With Olanzapine in Patients With Locally Advanced or Metastatic Upper Gastrointestinal and Lung Cancer"
          }
        ],
        "category": "China",
        "trial_count": 88
      },
      {
        "citations": [
          {
            "nct_id": "NCT07521618",
            "excerpt": "One-stop Diagnosis and Treatment for Suspected Lung Cancer: Combined RBS, nClE, OBCT and Ablation"
          },
          {
            "nct_id": "NCT07528170",
            "excerpt": "Complications After CT-guided Lung Biopsies at St. Olavs Hospital"
          },
          {
            "nct_id": "NCT06676917",
            "excerpt": "Datopotamab Deruxtecan (Dato-DXd) for Non-Small Cell Lung Cancer (NSCLC) Patients With Active Brain Metastases"
          },
          {
            "nct_id": "NCT04314297",
            "excerpt": "Anlotinib In Combination With Durvalumab As Sequential Therapy of Thoracic Radiotherapy After Induction Chemotherapy For Extensive-Stage Small Cell Lung Cancer:A Single Arm Study"
          },
          {
            "nct_id": "NCT00607425",
            "excerpt": "Saliva mRNA Expression Profiling for Early Stage Non-Small Cell Lung Cancer Screening"
          }
        ],
        "category": "Unknown",
        "trial_count": 43
      },
      {
        "citations": [
          {
            "nct_id": "NCT02149576",
            "excerpt": "Does Intense Regimented Surveillance Improve the Rates of Therapeutic Re-Intervention After Lung Cancer Surgery"
          },
          {
            "nct_id": "NCT04931017",
            "excerpt": "Metformin for Chemoprevention of Lung Cancer in Overweight or Obese Individuals at High Risk for Lung Cancer"
          },
          {
            "nct_id": "NCT02609776",
            "excerpt": "Study of Amivantamab, a Human Bispecific EGFR and cMet Antibody, in Participants With Advanced Non-Small Cell Lung Cancer"
          },
          {
            "nct_id": "NCT07144280",
            "excerpt": "A Study to Learn About the Study Medicine Called PF-08046054/SGN-PDL1V Versus Docetaxel in Adult Participants With Previously-Treated Programmed Cell Death Ligand 1 (PD-L1) Positive Non-Small-Cell Lun"
          },
          {
            "nct_id": "NCT01450761",
            "excerpt": "Trial in Extensive-Disease Small Cell Lung Cancer (ED-SCLC) Subjects Comparing Ipilimumab Plus Etoposide and Platinum Therapy to Etoposide and Platinum Therapy Alone"
          }
        ],
        "category": "Canada",
        "trial_count": 33
      },
      {
        "citations": [
          {
            "nct_id": "NCT04510454",
            "excerpt": "Evaluation of a ddPCR Technology for the SARS-CoV-2 Detection in Symptomatic Patients With Suspicion of COVID-19"
          },
          {
            "nct_id": "NCT07441941",
            "excerpt": "Single-Fraction Pulmonary Ablative Radiotherapy Outcomes and Quality-of-life Workup"
          },
          {
            "nct_id": "NCT03840915",
            "excerpt": "M7824 in Combination With Chemotherapy in Stage IV Non-small Cell Lung Cancer (NSCLC)"
          },
          {
            "nct_id": "NCT04504669",
            "excerpt": "First Time in Human Study of AZD8701 With or Without Durvalumab in Participants With Advanced Solid Tumours"
          },
          {
            "nct_id": "NCT06781983",
            "excerpt": "Safety and Tolerability of IPH4502 in Patients With Advanced Solid Tumors"
          }
        ],
        "category": "France",
        "trial_count": 26
      },
      {
        "citations": [
          {
            "nct_id": "NCT01510743",
            "excerpt": "Ultrasound Guided Central Vein Catheterization and Complications"
          },
          {
            "nct_id": "NCT00319514",
            "excerpt": "Weekly Versus 3-Weekly Docetaxel Plus Cisplatin for Advanced NSCLC"
          },
          {
            "nct_id": "NCT05528458",
            "excerpt": "Osimertinib to Suppress the Progression of Remaining GGN for EGFR Mutation-positive Stage IB-IIIA Lung Adenocarcinoma"
          },
          {
            "nct_id": "NCT01376856",
            "excerpt": "Characteristics of Mediastinal Lymph Node With False Positive FDG PET/CT Results in Lung Cancer Staging : Relation With TB and Latent TB Infection"
          },
          {
            "nct_id": "NCT03381274",
            "excerpt": "Oleclumab (MEDI9447) Epidermal Growth Factor Receptor Mutant (EGFRm) Non-small Cell Lung Cancer (NSCLC) Novel Combination Study"
          }
        ],
        "category": "South Korea",
        "trial_count": 16
      },
      {
        "citations": [
          {
            "nct_id": "NCT01999673",
            "excerpt": "Phase 3 Study of Bavituximab Plus Docetaxel Versus Docetaxel Alone in Patients With Late-stage Non-squamous Non-small-cell Lung Cancer"
          },
          {
            "nct_id": "NCT03705403",
            "excerpt": "IMMUNOtherapy and Stereotactic ABlative Radiotherapy (IMMUNOSABR) a Phase II Study"
          },
          {
            "nct_id": "NCT02552121",
            "excerpt": "Tisotumab Vedotin (HuMax®-TF-ADC) Safety Study in Patients With Solid Tumors"
          },
          {
            "nct_id": "NCT01846416",
            "excerpt": "A Study of Atezolizumab in Participants With Programmed Death-Ligand 1 (PD-L1) Positive Locally Advanced or Metastatic Non-Small Cell Lung Cancer (NSCLC) [FIR]"
          },
          {
            "nct_id": "NCT03125603",
            "excerpt": "Side Effects of Anti-PD-(L)-1 and Anti CTLA-A4 in the Non Small Cells Lung Cancer"
          }
        ],
        "category": "Belgium",
        "trial_count": 14
      },
      {
        "citations": [
          {
            "nct_id": "NCT02603627",
            "excerpt": "Prevalence of COPD in Our Lung Cancer Population, Compared to Controls"
          },
          {
            "nct_id": "NCT02128724",
            "excerpt": "Palliative Thoracic Radiotherapy Plus BKM120"
          },
          {
            "nct_id": "NCT05230888",
            "excerpt": "Comprehensive Geriatric Assessment in Elderly Non-Small Cell Lung Cancer Patients"
          },
          {
            "nct_id": "NCT00454376",
            "excerpt": "Disease-Specific Questionnaire in Assessing Quality of Life in Patients With Gastrointestinal-Related Neuroendocrine Tumors"
          },
          {
            "nct_id": "NCT01460693",
            "excerpt": "Comparison of Imatinib Versus Dasatinib in Patients With Newly-diagnosed Chronic Phase Chronic Myeloid Leukaemia"
          }
        ],
        "category": "United Kingdom",
        "trial_count": 13
      },
      {
        "citations": [
          {
            "nct_id": "NCT07164313",
            "excerpt": "A Study of ZW251 in Participants With Advanced Solid Tumors"
          },
          {
            "nct_id": "NCT02157883",
            "excerpt": "Study to Assess the Effect of Itraconazole (a CYP3A4 Inhibitor) on the Pharmacokinetics of AZD9291, in Patients With EGFR Positive Non-small Cell Lung Cancer. Patients Will be Chosen From Those Who Ha"
          },
          {
            "nct_id": "NCT05617742",
            "excerpt": "Comparison of 68Ga-FAPI-46 PET and 18F-FDG PET in Lung Cancer"
          },
          {
            "nct_id": "NCT02310464",
            "excerpt": "Trial of Active Immunotherapy With OBI-833 (Globo H-CRM197) in Advanced/Metastatic Gastric, Lung, Colorectal or Breast Cancer Subjects"
          },
          {
            "nct_id": "NCT04974632",
            "excerpt": "Mobile 3D C-arm CT for Lung Tumor Localization Efficacy Analysis: a Prospective Clinical Trial"
          }
        ],
        "category": "Taiwan",
        "trial_count": 11
      },
      {
        "citations": [
          {
            "nct_id": "NCT04878796",
            "excerpt": "Effectiveness of mRNA Covid-19 Vaccines on Cancer Patients:Observational Study. (ANTICOV)"
          },
          {
            "nct_id": "NCT02883790",
            "excerpt": "Effects of Somnage® in the Management on Sleep and Mood in Cancer Patients"
          },
          {
            "nct_id": "NCT07303218",
            "excerpt": "The HER Project: HRD in EGFR-mutated NSCLC"
          },
          {
            "nct_id": "NCT03911193",
            "excerpt": "CABozantinib in Non-Small Cell Lung Cancer (NSCLC) Patients With MET Deregulation"
          },
          {
            "nct_id": "NCT03546426",
            "excerpt": "Pembrolizumab Plus Autologous Dendritic Cell Vaccine in Patients with PD-L1 Negative Advanced Mesothelioma Who Have Failed Prior Therapies"
          }
        ],
        "category": "Italy",
        "trial_count": 11
      },
      {
        "citations": [
          {
            "nct_id": "NCT01141842",
            "excerpt": "Early Detection of Lung Tumors by Sniffer Dogs - Evaluation of Sensitivity and Specificity"
          },
          {
            "nct_id": "NCT04602533",
            "excerpt": "Efficacy and Safety of Standard of Care Plus Durvalumab in Patients With Limited Disease Small Cell Lung Cancer (DOLPHIN)"
          },
          {
            "nct_id": "NCT06093334",
            "excerpt": "Imaging of Chemotherapy-induced Morphological and Functional Lung Changes in Childhood ALL and HD"
          },
          {
            "nct_id": "NCT00610844",
            "excerpt": "Preoperative Percutaneous Radiofrequency Ablation of Primary and Secondary Lung Tumors"
          },
          {
            "nct_id": "NCT04335409",
            "excerpt": "Pneumonitis After Radiotherapy for Lung Cancer"
          }
        ],
        "category": "Germany",
        "trial_count": 8
      },
      {
        "citations": [
          {
            "nct_id": "NCT01963923",
            "excerpt": "Effectiveness of a Preoperative Pulmonary Rehabilitation Program in Patients Awaiting Lung Resection"
          },
          {
            "nct_id": "NCT04285866",
            "excerpt": "Spanish Real World Data on Patients Treated With Durvalumab After Chemoradiotherapy."
          },
          {
            "nct_id": "NCT05600569",
            "excerpt": "Registry of the Spanish Society of Thoracic Surgery"
          },
          {
            "nct_id": "NCT06870487",
            "excerpt": "A Study to Learn About the Study Medicine Called PF-08046032 in People With Advanced Cancers"
          },
          {
            "nct_id": "NCT04677309",
            "excerpt": "LUS to Assess Lung Injury After Lung Resection"
          }
        ],
        "category": "Spain",
        "trial_count": 8
      },
      {
        "citations": [
          {
            "nct_id": "NCT01166204",
            "excerpt": "Concurrent and Non-concurrent Chemo-radiotherapy or Radiotherapy Alone With Intensity-modulated Radiotherapy (IMRT) for Non Small Cell Lung Cancer (NSCLC) to an Individualised Mean Lung Dose (MLD)"
          },
          {
            "nct_id": "NCT05401786",
            "excerpt": "Anti-PD-1 Re-challenge After Immune Priming by Ipilimumab and Immune Boosting by Radiotherapy in Advanced NSCLC"
          },
          {
            "nct_id": "NCT05748093",
            "excerpt": "Improving Osimertinib Exposure and Cost-effectiveness Using Pharmacokinetic Boosting With Cobicistat"
          },
          {
            "nct_id": "NCT06809946",
            "excerpt": "Feasibility of Fluorescence Imaging With Bevacizumab-800CW During Bronchoscopy"
          },
          {
            "nct_id": "NCT00953459",
            "excerpt": "Sunitinib Malate in Treating Patients With Small Cell Lung Cancer"
          }
        ],
        "category": "Netherlands",
        "trial_count": 8
      },
      {
        "citations": [
          {
            "nct_id": "NCT04385147",
            "excerpt": "Advanced Endoscopy During COVID-19"
          },
          {
            "nct_id": "NCT01570296",
            "excerpt": "A Trial of Gefitinib in Combination With BKM120 in Patients With Advanced Non-Small Cell Lung Cancer, With Enrichment for Patients Whose Tumours Harbour Molecular Alterations of PI3K Pathway and Known"
          },
          {
            "nct_id": "NCT05801029",
            "excerpt": "A Study to Investigate Safety and Efficacy of Osimertinib and Amivantamab in Participants With Non-small Cell Lung Cancer With Common Epidermal Growth Factor Receptor Mutations"
          },
          {
            "nct_id": "NCT07358715",
            "excerpt": "Liquid Biopsy-Based Pre-Screening to Streamline LDCT Lung Cancer Screening in High-Risk Individuals"
          },
          {
            "nct_id": "NCT05236608",
            "excerpt": "A Study to Evaluate the Combination of Nivolumab With ADG106 in Metastatic NSCLC"
          }
        ],
        "category": "Singapore",
        "trial_count": 7
      },
      {
        "citations": [
          {
            "nct_id": "NCT05212922",
            "excerpt": "A Study to Evaluate YH001 in Combination With Toripalimab in Subjects With Advanced NSCLC and HCC"
          },
          {
            "nct_id": "NCT04654364",
            "excerpt": "Lung Cancer Registry"
          },
          {
            "nct_id": "NCT00291850",
            "excerpt": "Phase II Trial of Dose-dense Paclitaxel and Cisplatin as Neo-adjuvant Chemotherapy for Operable Stage II and IIA NSCLC"
          },
          {
            "nct_id": "NCT00432315",
            "excerpt": "Docetaxel in Non Small Cell Lung Cancer (NSCLC)"
          },
          {
            "nct_id": "NCT04584775",
            "excerpt": "Implementing Acupuncture and Chinese Herbal Medicine Into Palliative Care"
          }
        ],
        "category": "Austria",
        "trial_count": 5
      },
      {
        "citations": [
          {
            "nct_id": "NCT07398027",
            "excerpt": "Post-Market Study of Transbronchial Cryo-assisted RFA During Robotic Bronchoscopy With Subsequent Surgical Resection"
          },
          {
            "nct_id": "NCT01089998",
            "excerpt": "PET/CT Imaging for Radiation Dosimetry, Plasma Pharmacokinetics, Safety and Tolerability in Healthy Volunteers and Safety, Tolerability and Diagnostic Performance of BAY86-9596 in Patients With Non-sm"
          },
          {
            "nct_id": "NCT05275868",
            "excerpt": "Study of MGY825 in Patients With Advanced Non-small Cell Lung Cancer"
          },
          {
            "nct_id": "NCT02069158",
            "excerpt": "Dose Finding Study Of PF-05212384 With Paclitaxel And Carboplatin In Patients With Advanced Solid Tumor"
          },
          {
            "nct_id": "NCT00030745",
            "excerpt": "Combination Chemotherapy Before Surgery in Treating Patients With Mesothelioma of the Lung"
          }
        ],
        "category": "Switzerland",
        "trial_count": 5
      },
      {
        "citations": [
          {
            "nct_id": "NCT04052971",
            "excerpt": "To Evaluate the Safety, Pharmacokinetics, Pharmacodynamics, and Antitumor Activity of ABN401 in Patients With Advanced Solid Tumors and Non-Small Cell Lung Cancer Harboring c-MET Dysregulation"
          },
          {
            "nct_id": "NCT06127654",
            "excerpt": "Ventilation Imaging to Improve the Quality of Life for Patients With Lung Cancer Treated With Radiation Therapy"
          },
          {
            "nct_id": "NCT02824965",
            "excerpt": "Pembrolizumab + CVA21 in Advanced NSCLC"
          },
          {
            "nct_id": "NCT07353957",
            "excerpt": "Study to Investigate Petosemtamab in Adults With Metastatic Non-Small Cell Lung Cancer"
          },
          {
            "nct_id": "NCT05858736",
            "excerpt": "Safety, PK and Efficacy of AI-061 in Advanced Solid Tumors"
          }
        ],
        "category": "Australia",
        "trial_count": 5
      },
      {
        "citations": [
          {
            "nct_id": "NCT03521154",
            "excerpt": "A Global Study to Assess the Effects of Osimertinib Following Chemoradiation in Patients With Stage III Unresectable Non-small Cell Lung Cancer (LAURA)"
          },
          {
            "nct_id": "NCT06120283",
            "excerpt": "BGB-43395 Alone or as Part of Combination Therapies in Participants With Breast Cancer and Other Advanced Solid Tumors"
          },
          {
            "nct_id": "NCT07279948",
            "excerpt": "A Single-arm Observational Study to Characterize the Demographic, Clinical Features and Outcomes of a Brazilian Cohort of Patients With Lung Cancer."
          },
          {
            "nct_id": "NCT06822543",
            "excerpt": "A Single Arm, Phase 2 Study of Datopotamab Deruxtecan, Carboplatin, and Pembrolizumab for Treatment-naive Brain Metastases From NSCLC (Non-small Cell Lung Cancer)"
          }
        ],
        "category": "Brazil",
        "trial_count": 4
      },
      {
        "citations": [
          {
            "nct_id": "NCT06646770",
            "excerpt": "SEgmentectomy Versus Lobectomy in T1C Non-Small Cell Lung Cancer (SELTIC)"
          },
          {
            "nct_id": "NCT05005273",
            "excerpt": "A Study to Assess BMS-986207 in Combination With Nivolumab and Ipilimumab as First-line Treatment for Participants With Stage IV Non-Small Cell Lung Cancer"
          },
          {
            "nct_id": "NCT05290480",
            "excerpt": "Expiratory Muscle Training Versus Incentive Spirometry After Colorectal Surgery"
          },
          {
            "nct_id": "NCT06712316",
            "excerpt": "Safety, Efficacy, and Pharmacokinetics of BNT327 in Combination With Chemotherapy and Other Investigational Agents for Lung Cancer"
          }
        ],
        "category": "Turkey (Türkiye)",
        "trial_count": 4
      },
      {
        "citations": [
          {
            "nct_id": "NCT00752115",
            "excerpt": "Combination Chemotherapy With Sildenafil Plus Carboplatin and Paclitaxel in Patients With Advanced Non-small Cell Lung Cancer"
          },
          {
            "nct_id": "NCT06603987",
            "excerpt": "Using CICS-1 and SPM-011 and ［18F］FBPA Commissioned by CICS and Sumitomo Heavy Industries and STELLA PHARMA"
          },
          {
            "nct_id": "NCT05258279",
            "excerpt": "Lenvatinib in Combination With Carboplatin Pemetrexed and Pembrolizumab for NSCLC With EGFR Mutations"
          },
          {
            "nct_id": "NCT03410108",
            "excerpt": "Phase 2 Study of Brigatinib in Japanese Participants With Anaplastic Lymphoma Kinase (ALK)-Positive Non-Small Cell Lung Cancer (NSCLC)"
          }
        ],
        "category": "Japan",
        "trial_count": 4
      }
    ]
  },
  "meta": {
    "filters_applied": {
      "condition": "lung cancer"
    },
    "source": "ClinicalTrials.gov v2 API",
    "query_interpretation": "Identify the countries that conduct the highest number of clinical trials for lung cancer.",
    "assumptions": [
      "Visualization type determined by rule-based fallback"
    ],
    "trial_count": 500,
    "total_matching": 14166,
    "phase_filter_mode": "inclusive_hybrid"
  }
}
```

---

### (3) Query

```
Compare phases for trials involving Metformin vs Insulin
```

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare phases for trials involving Metformin vs Insulin"
  }' | jq
```

### (3) Answer

```json
{
  "visualization": {
    "type": "grouped_bar_chart",
    "title": "Compare clinical trials involving Metformin and Insulin across different phases.",
    "encoding": {
      "x": {
        "field": "category",
        "type": "nominal"
      },
      "y": {
        "field": "trial_count",
        "type": "quantitative"
      },
      "series": {
        "field": "entity",
        "type": "nominal"
      }
    },
    "data": [
      {
        "citations": [
          {
            "nct_id": "NCT00993473",
            "excerpt": "6-month Comparison of Morning Lantus Versus Neutral Protamine Hagedorn Insulin in Young Children With Type 1 Diabetes"
          },
          {
            "nct_id": "NCT00653341",
            "excerpt": "Effect of Insulin Glargine in Insulin Naïve Subjects With Type 2 Diabetes on Oral Hypoglycemic Agent(s)"
          },
          {
            "nct_id": "NCT02856113",
            "excerpt": "Phase 3 Alogliptin Pediatric Study"
          },
          {
            "nct_id": "NCT03874715",
            "excerpt": "Comparison of SAR341402 to NovoLog in Adult Patients With Type 1 Diabetes Mellitus Also Using Insulin Glargine"
          },
          {
            "nct_id": "NCT01531114",
            "excerpt": "PraSugrel vs TicagrElor in ST-Elevation Myocardial Infarction paTients With Diabetes Mellitus"
          }
        ],
        "entity": "Insulin",
        "category": "Phase 3",
        "trial_count": 63
      },
      {
        "citations": [
          {
            "nct_id": "NCT00837759",
            "excerpt": "Novel Therapy to Preserve Beta Cell Function in New Onset Type 1 Diabetes"
          },
          {
            "nct_id": "NCT00018382",
            "excerpt": "Insulin, Neurogenetics and Memory in Alzheimer's Disease"
          },
          {
            "nct_id": "NCT06528405",
            "excerpt": "The Efficacy and Safety of Sodium-glucose Cotransporter 2 Inhibitors in Patients With Acute Kidney Disease"
          },
          {
            "nct_id": "NCT00279305",
            "excerpt": "Rituximab in New Onset Type 1 Diabetes"
          },
          {
            "nct_id": "NCT07041268",
            "excerpt": "Immunotherapy of the Recent-onset Type 1 Diabetes in Adolescents With Repeated Courses of Rituximab"
          }
        ],
        "entity": "Insulin",
        "category": "Phase 2",
        "trial_count": 61
      },
      {
        "citations": [
          {
            "nct_id": "NCT03011008",
            "excerpt": "Liraglutide as Additional Treatment to Insulin in Patients With Autoimmune Diabetes Mellitus"
          },
          {
            "nct_id": "NCT00133718",
            "excerpt": "A 2 Year Trial of Patients With Type 2 Diabetes Focusing on Cardiovascular Diagnostics and Metabolic Control"
          },
          {
            "nct_id": "NCT00521690",
            "excerpt": "The Effect of Insulin Detemir on Blood Glucose Control in Taiwanese Patients With Type 2 Diabetes Failing on OAD"
          },
          {
            "nct_id": "NCT00274274",
            "excerpt": "Efficacy and Safety of a Fixed or a Flexible Supplementary Insulin Therapy in Type 2 Diabetes"
          },
          {
            "nct_id": "NCT00627471",
            "excerpt": "Type 2 Diabetes Management With Lantus® (Malbec: Manejo Con Lantus® de Diabéticos Tipo 2)"
          }
        ],
        "entity": "Insulin",
        "category": "Phase 4",
        "trial_count": 54
      },
      {
        "citations": [
          {
            "nct_id": "NCT02562313",
            "excerpt": "A Trial Investigating the Continuous Subcutaneous Insulin Infusion of a Liquid Formulation of BioChaperone Insulin Lispro in Comparison to Humalog®"
          },
          {
            "nct_id": "NCT02328040",
            "excerpt": "Randomized Trial Comparing Sitagliptin to Placebo in Closed Loop"
          },
          {
            "nct_id": "NCT07319286",
            "excerpt": "Role of Glucagon-like Peptide-1 Receptor Agonists in Menstrual Irregularities in Adolescent Females With Type 1 Diabetes Mellitus"
          },
          {
            "nct_id": "NCT01193387",
            "excerpt": "Comparison of Two Identical NN1250 Formulations in Healthy Volunteers"
          },
          {
            "nct_id": "NCT01769404",
            "excerpt": "A Study of LY2605541 and Glargine in Participants With Type 1 Diabetes"
          }
        ],
        "entity": "Insulin",
        "category": "Phase 1",
        "trial_count": 45
      },
      {
        "citations": [
          {
            "nct_id": "NCT01680926",
            "excerpt": "Metabolic Activation With Almased for Type 2 Diabetes Patients"
          },
          {
            "nct_id": "NCT01929798",
            "excerpt": "Crossover Feasibility Study of Portable AP Device With Zone-MPC and HMS and Adapted I:C and Basal Insulin"
          },
          {
            "nct_id": "NCT03566225",
            "excerpt": "Pioglitazone Versus Metformin as First Treatment in Infertile Women With Polycystic Ovary Syndrome"
          },
          {
            "nct_id": "NCT03469492",
            "excerpt": "Investigating the Role of the Polyol Pathway in the Central Nervous System Production of Fructose"
          },
          {
            "nct_id": "NCT01817400",
            "excerpt": "Mediators of Abnormal Reproductive Function in Obesity (MARO)"
          }
        ],
        "entity": "Insulin",
        "category": "Early Phase 1",
        "trial_count": 8
      },
      {
        "citations": [
          {
            "nct_id": "NCT05505994",
            "excerpt": "The Efficacy and Safety of DWP16001 in Combination With Metformin in T2DM Patients Inadequately Controlled on Metformin"
          },
          {
            "nct_id": "NCT05532813",
            "excerpt": "Evaluation of the Efficacy and Safety of Metformin in the Myotonic Dystrophy Type 1 (Steinert's Disease)"
          },
          {
            "nct_id": "NCT00316082",
            "excerpt": "Study of BMS-477118 as Monotherapy With Titration in Subjects With Type 2 Diabetes Who Are Not Controlled With Diet and Exercise"
          },
          {
            "nct_id": "NCT04504396",
            "excerpt": "Safety and Efficacy of PB-119 in Subjects With Type 2 Diabetes and Not Well-controlled by Metformin Monotherapy"
          },
          {
            "nct_id": "NCT02856113",
            "excerpt": "Phase 3 Alogliptin Pediatric Study"
          }
        ],
        "entity": "Metformin",
        "category": "Phase 3",
        "trial_count": 119
      },
      {
        "citations": [
          {
            "nct_id": "NCT02495103",
            "excerpt": "Vandetanib in Combination With Metformin in People With HLRCC or SDH-Associated Kidney Cancer or Sporadic Papillary Renal Cell Carcinoma"
          },
          {
            "nct_id": "NCT06528405",
            "excerpt": "The Efficacy and Safety of Sodium-glucose Cotransporter 2 Inhibitors in Patients With Acute Kidney Disease"
          },
          {
            "nct_id": "NCT04931017",
            "excerpt": "Metformin for Chemoprevention of Lung Cancer in Overweight or Obese Individuals at High Risk for Lung Cancer"
          },
          {
            "nct_id": "NCT03235050",
            "excerpt": "A Study to Evaluate the Efficacy and Safety of MEDI0382 in the Treatment of Overweight and Obese Subjects With Type 2 Diabetes"
          },
          {
            "nct_id": "NCT03230786",
            "excerpt": "Study to Evaluate the Efficacy and Safety of KBP-042 in Patients With Type 2 Diabetes"
          }
        ],
        "entity": "Metformin",
        "category": "Phase 2",
        "trial_count": 108
      },
      {
        "citations": [
          {
            "nct_id": "NCT04593459",
            "excerpt": "Probiotic Intervention in PCOS"
          },
          {
            "nct_id": "NCT00133718",
            "excerpt": "A 2 Year Trial of Patients With Type 2 Diabetes Focusing on Cardiovascular Diagnostics and Metabolic Control"
          },
          {
            "nct_id": "NCT00672464",
            "excerpt": "Cardio Risk of Acute Schizophrenia Olanzapine Duke"
          },
          {
            "nct_id": "NCT03570632",
            "excerpt": "Metformin for Preeclampsia Prevention in Pregnant Women With Type 1 Diabetes Mellitus"
          },
          {
            "nct_id": "NCT01785043",
            "excerpt": "Differences in Endothelial Function Amongst Sitagliptin and Liraglutide Users"
          }
        ],
        "entity": "Metformin",
        "category": "Phase 4",
        "trial_count": 103
      },
      {
        "citations": [
          {
            "nct_id": "NCT02495103",
            "excerpt": "Vandetanib in Combination With Metformin in People With HLRCC or SDH-Associated Kidney Cancer or Sporadic Papillary Renal Cell Carcinoma"
          },
          {
            "nct_id": "NCT00899470",
            "excerpt": "Bioequivalence Study of Saxagliptin and Glucophage Combination Formulations in Healthy Subjects (A)"
          },
          {
            "nct_id": "NCT01693289",
            "excerpt": "Study to Compare Between Combimed Metformin-letrozole and Ovarian Drilling in Pcos With Bilateral Ovarian Drilling in Clomiphene-resistant Infertile Women With Polycystic Ovarian Syndrome"
          },
          {
            "nct_id": "NCT00894322",
            "excerpt": "A Study to Examine the Pharmacokinetics, Tolerability, Safety and Efficacy of Exenatide Once Weekly Suspension"
          },
          {
            "nct_id": "NCT03629054",
            "excerpt": "This Study in Healthy People Tests Whether Taking a Low Strength of Empagliflozin, Linagliptin, and Metformin Together in 1 Pill is the Same as Taking Them in Separate Pills"
          }
        ],
        "entity": "Metformin",
        "category": "Phase 1",
        "trial_count": 88
      },
      {
        "citations": [
          {
            "nct_id": "NCT03772262",
            "excerpt": "Assessing Goldenseal-drug Interactions Using a Probe Drug Cocktail Approach"
          },
          {
            "nct_id": "NCT03566225",
            "excerpt": "Pioglitazone Versus Metformin as First Treatment in Infertile Women With Polycystic Ovary Syndrome"
          },
          {
            "nct_id": "NCT03681197",
            "excerpt": "Metformin Use and Clinical Pregnancy Rate in Women With Unexplained Infertility"
          },
          {
            "nct_id": "NCT06185179",
            "excerpt": "Metformin and Muscle Recovery"
          },
          {
            "nct_id": "NCT06628544",
            "excerpt": "Trained Immunity in Fungal Infection and Its Mechanism"
          }
        ],
        "entity": "Metformin",
        "category": "Early Phase 1",
        "trial_count": 12
      }
    ]
  },
  "meta": {
    "filters_applied": {},
    "source": "ClinicalTrials.gov v2 API",
    "query_interpretation": "Compare clinical trials involving Metformin and Insulin across different phases.",
    "assumptions": [
      "Visualization type determined by rule-based fallback"
    ],
    "trial_count": 962,
    "total_matching": 1000,
    "phase_filter_mode": "inclusive_hybrid",
    "comparison_insight": "Insulin is concentrated in Phase 3 (27% of trials), while Metformin is concentrated in Phase 3 (28% of trials)."
  }
}
```

---

### (4) Query

```
Which diabetes studies have unusually high enrollment?
```

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Which diabetes studies have unusually high enrollment?"
  }' | jq
```

### (4) Answer

```json
{
  "visualization": {
    "type": "scatter_plot",
    "title": "Identify diabetes clinical studies with unusually high enrollment.",
    "encoding": {
      "x": {
        "field": "enrollment",
        "type": "quantitative"
      },
      "y": {
        "field": "z_score",
        "type": "quantitative"
      },
      "color": {
        "field": "phase_str",
        "type": "nominal"
      },
      "label": {
        "field": "nct_id",
        "type": "nominal"
      }
    },
    "data": [
      {
        "citations": [
          {
            "nct_id": "NCT02138097",
            "excerpt": "Oral and Non-insulin Injected Hypoglycemic Therapy Utilization Patterns"
          }
        ],
        "nct_id": "NCT02138097",
        "brief_title": "Oral and Non-insulin Injected Hypoglycemic Therapy Utilization Patterns",
        "enrollment": 615067.0,
        "z_score": 21.15,
        "phase_str": "NA",
        "status": "COMPLETED",
        "sponsor": "Boehringer Ingelheim"
      },
      {
        "citations": [
          {
            "nct_id": "NCT02857764",
            "excerpt": "Sodium-glucose Co-transporter 2 (SGLT2) Inhibitor Risk of Below-Knee Lower Extremity Amputation: A Retrospective Cohort Study Using a Large Claims Database in the United States"
          }
        ],
        "nct_id": "NCT02857764",
        "brief_title": "Sodium-glucose Co-transporter 2 (SGLT2) Inhibitor Risk of Below-Knee Lower Extremity Amputation: A Retrospective Cohort Study Using a Large Claims Database in the United States",
        "enrollment": 127690.0,
        "z_score": 4.33,
        "phase_str": "NA",
        "status": "COMPLETED",
        "sponsor": "Janssen Research & Development, LLC"
      },
      {
        "citations": [
          {
            "nct_id": "NCT02812303",
            "excerpt": "Implementation of a Population Health Chronic Disease Management Program"
          }
        ],
        "nct_id": "NCT02812303",
        "brief_title": "Implementation of a Population Health Chronic Disease Management Program",
        "enrollment": 108000.0,
        "z_score": 3.65,
        "phase_str": "NA",
        "status": "COMPLETED",
        "sponsor": "Massachusetts General Hospital"
      },
      {
        "citations": [
          {
            "nct_id": "NCT02487888",
            "excerpt": "A Study of the Impact of Genetic Testing on Clinical Decision Making and Patient Care"
          }
        ],
        "nct_id": "NCT02487888",
        "brief_title": "A Study of the Impact of Genetic Testing on Clinical Decision Making and Patient Care",
        "enrollment": 100000.0,
        "z_score": 3.37,
        "phase_str": "NA",
        "status": "UNKNOWN",
        "sponsor": "Proove Bioscience, Inc."
      }
    ]
  },
  "meta": {
    "filters_applied": {
      "condition": "diabetes"
    },
    "source": "ClinicalTrials.gov v2 API",
    "query_interpretation": "Identify diabetes clinical studies with unusually high enrollment.",
    "assumptions": [
      "Visualization type determined by rule-based fallback"
    ],
    "trial_count": 500,
    "total_matching": 23841,
    "phase_filter_mode": "inclusive_hybrid"
  }
}
```

---

### (5) Query

```
Show phase 3 diabetes trials in South Korea
```

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show phase 3 diabetes trials in South Korea",
    "condition": "diabetes",
    "phase": ["Phase 3"],
    "country": "South Korea"
  }' | jq
```

### (5) Answer

```json
{
  "visualization": {
    "type": "bar_chart",
    "title": "Show the distribution of Phase 3 diabetes clinical trials conducted in South Korea.",
    "encoding": {
      "x": {
        "field": "category",
        "type": "nominal"
      },
      "y": {
        "field": "trial_count",
        "type": "quantitative"
      }
    },
    "data": [
      {
        "citations": [
          {
            "nct_id": "NCT05504226",
            "excerpt": "Clinical Efficacy and Safety Evaluation of Teneligliptin in Type 2 Diabetes Who Have Inadequate GlycemIc Control With Empaglyflozin 25 mg and Metformin"
          },
          {
            "nct_id": "NCT04041167",
            "excerpt": "Impact of Lipoic Acid Use on Stroke Outcome After Reperfusion Therapy in Patients With Diabetes (IMPORTANT)"
          },
          {
            "nct_id": "NCT05226897",
            "excerpt": "Clinical Trial to Assess the Efficacy and Safety of YYC405 in Type 2 Diabetes Patients"
          },
          {
            "nct_id": "NCT02946632",
            "excerpt": "Effectiveness & Tolerability of Novel, Initial Triple Combination Therapy vs Conventional Therapy in Type 2 Diabetes"
          },
          {
            "nct_id": "NCT03713684",
            "excerpt": "Efficacy and Safety of Efpeglenatide Versus Placebo in Patients With Type 2 Diabetes Mellitus Inadequately Controlled With Basal Insulin Alone or in Combination With Oral Antidiabetic Drug(s)"
          }
        ],
        "category": "South Korea",
        "trial_count": 50
      },
      {
        "citations": [
          {
            "nct_id": "NCT00516048",
            "excerpt": "An Exploratory Study of the Effect of Treatment Interruption on Safety of Exenatide in Patients With Type 2 Diabetes"
          },
          {
            "nct_id": "NCT02545049",
            "excerpt": "Efficacy and Safety of Finerenone in Subjects With Type 2 Diabetes Mellitus and the Clinical Diagnosis of Diabetic Kidney Disease"
          },
          {
            "nct_id": "NCT03315143",
            "excerpt": "Effect of Sotagliflozin on Cardiovascular and Renal Events in Participants With Type 2 Diabetes and Moderate Renal Impairment Who Are at Cardiovascular Risk"
          },
          {
            "nct_id": "NCT01790438",
            "excerpt": "A Study to Compare a New Long-Acting Insulin (LY2605541) and Human Insulin NPH in Participants With Type 2 Diabetes"
          },
          {
            "nct_id": "NCT04255433",
            "excerpt": "A Study of Tirzepatide (LY3298176) Compared With Dulaglutide on Major Cardiovascular Events in Participants With Type 2 Diabetes"
          }
        ],
        "category": "Canada",
        "trial_count": 39
      },
      {
        "citations": [
          {
            "nct_id": "NCT02302716",
            "excerpt": "A Study of LY2963016 Compared to LANTUS® in Adult Participants With Type 2 Diabetes Mellitus"
          },
          {
            "nct_id": "NCT00614120",
            "excerpt": "Effect of Liraglutide or Glimepiride Added to Metformin on Blood Glucose Control in Subjects With Type 2 Diabetes"
          },
          {
            "nct_id": "NCT00713830",
            "excerpt": "GLP-1 Receptor Agonist Lixisenatide in Patients With Type 2 Diabetes for Glycemic Control and Safety Evaluation, on Top of Sulfonylurea"
          },
          {
            "nct_id": "NCT00900146",
            "excerpt": "Dose Finding, Safety and Efficacy of Monthly Subcutaneous Canakinumab Administration in Metformin Monotherapy Treated Type 2 Diabetic Patients"
          },
          {
            "nct_id": "NCT00688701",
            "excerpt": "GLP-1 Receptor Agonist Lixisenatide in Patients With Type 2 Diabetes for Glycemic Control and Safety Evaluation in Monotherapy"
          }
        ],
        "category": "India",
        "trial_count": 12
      },
      {
        "citations": [
          {
            "nct_id": "NCT05362058",
            "excerpt": "A Study of Insulin Efsitora Alfa (LY3209590) Compared to Degludec in Adults With Type 2 Diabetes Who Are Starting Basal Insulin for the First Time"
          },
          {
            "nct_id": "NCT03429543",
            "excerpt": "Diabetes Study of Linagliptin and Empagliflozin in Children and Adolescents (DINAMO)TM"
          },
          {
            "nct_id": "NCT02662569",
            "excerpt": "Safety and Efficacy of Evolocumab in Combination With Statin Therapy in Adults With Diabetes and Hyperlipidemia or Mixed Dyslipidemia"
          },
          {
            "nct_id": "NCT07533175",
            "excerpt": "AMAZE 2: A Research Study Investigating How Well the Medicine NNC0487-0111 Helps People With Excess Body Weight and Type 2 Diabetes Lose Weight"
          },
          {
            "nct_id": "NCT04251156",
            "excerpt": "Research Study of How Well Semaglutide Works in People Living With Overweight or Obesity."
          }
        ],
        "category": "Brazil",
        "trial_count": 8
      },
      {
        "citations": [
          {
            "nct_id": "NCT01647542",
            "excerpt": "Study to Evaluate the Efficacy and Safety of Daily Oral TAK-875 25 and 50mg in Asia Pacific Adults With Type 2 Diabetes"
          },
          {
            "nct_id": "NCT01505426",
            "excerpt": "A Study to Assess the Efficacy and Safety of ASP1941 in Combination With Metformin in Asian Diabetes Patients"
          },
          {
            "nct_id": "NCT01644500",
            "excerpt": "A Study Comparing the Effects and Safety of Dulaglutide With Glimepiride in Type 2 Diabetes Mellitus"
          },
          {
            "nct_id": "NCT01059812",
            "excerpt": "A Pan Asian Trial Comparing Efficacy and Safety of NN5401 and Biphasic Insulin Aspart 30 in Type 2 Diabetes"
          },
          {
            "nct_id": "NCT01890122",
            "excerpt": "Efficacy and Safety of Alogliptin and Metformin Fixed-Dose Combination in Participants With Type 2 Diabetes"
          }
        ],
        "category": "Taiwan",
        "trial_count": 7
      },
      {
        "citations": [
          {
            "nct_id": "NCT01128894",
            "excerpt": "A Study to Determine the Efficacy and Safety of Albiglutide as Compared With Liraglutide."
          },
          {
            "nct_id": "NCT00251940",
            "excerpt": "GALLANT 7 Tesaglitazar Add-on to Sulphonylurea"
          },
          {
            "nct_id": "NCT01233622",
            "excerpt": "Safety and Efficacy of Galvus as add-on Therapy to Metformin Plus Glimepiride"
          },
          {
            "nct_id": "NCT00318422",
            "excerpt": "Effect of Liraglutide on Blood Glucose Control in Subjects With Type 2 Diabetes"
          },
          {
            "nct_id": "NCT01549964",
            "excerpt": "Comparison of Fasiglifam (TAK-875) to Placebo and Sitagliptin in Combination With Metformin in Participants With Type 2 Diabetes"
          }
        ],
        "category": "Australia",
        "trial_count": 5
      },
      {
        "citations": [
          {
            "nct_id": "NCT02849080",
            "excerpt": "Efficacy and Safety of Oral Semaglutide Using a Flexible Dose Adjustment Based on Clinical Evaluation Versus Sitagliptin in Subjects With Type 2 Diabetes Mellitus."
          },
          {
            "nct_id": "NCT00851903",
            "excerpt": "Evaluation of Insulin Glargine in Combination With Sitagliptin in Type 2 Diabetes Patients: EASIE Extension Trial"
          },
          {
            "nct_id": "NCT03882970",
            "excerpt": "A Study of Tirzepatide (LY3298176) Versus Insulin Degludec in Participants With Type 2 Diabetes"
          }
        ],
        "category": "Austria",
        "trial_count": 3
      },
      {
        "citations": [
          {
            "nct_id": "NCT01365507",
            "excerpt": "Efficacy and Safety of Insulin Degludec/Insulin Aspart in Insulin-naïve Subjects With Type 2 Diabetes Using Two Dosing Regimens"
          },
          {
            "nct_id": "NCT02294474",
            "excerpt": "Comparison of SAR342434 to Humalog as the Rapid Acting Insulin in Adult Patients With Type 2 Diabetes Mellitus Also Using Insulin Glargine"
          },
          {
            "nct_id": "NCT00174642",
            "excerpt": "Opposing Step-by-step Insulin Reinforcement to Intensified Strategy"
          }
        ],
        "category": "Turkey (Türkiye)",
        "trial_count": 3
      },
      {
        "citations": [
          {
            "nct_id": "NCT01137812",
            "excerpt": "The CANTATA-D2 Trial (CANagliflozin Treatment And Trial Analysis - DPP-4 Inhibitor Second Comparator Trial)"
          },
          {
            "nct_id": "NCT02096705",
            "excerpt": "Phase III Insulin Add-On Asia Regional Program - ST"
          },
          {
            "nct_id": "NCT03285308",
            "excerpt": "A Safety and Efficacy Study of Relamorelin in Diabetic Gastroparesis 01"
          }
        ],
        "category": "Singapore",
        "trial_count": 3
      },
      {
        "citations": [
          {
            "nct_id": "NCT01159600",
            "excerpt": "Efficacy and Safety Study With Empagliflozin (BI 10773) vs. Placebo as add-on to Metformin or Metformin Plus Sulfonylurea Over 24 Weeks in Patients With Type 2 Diabetes"
          },
          {
            "nct_id": "NCT01289990",
            "excerpt": "Safety and Efficacy of Empagliflozin (BI 10773) and Sitagliptin Versus Placebo Over 76 Weeks in Patients With Type 2 Diabetes"
          }
        ],
        "category": "Slovenia",
        "trial_count": 2
      },
      {
        "citations": [
          {
            "nct_id": "NCT01421459",
            "excerpt": "A Study in Adults With Type 2 Diabetes"
          },
          {
            "nct_id": "NCT05275400",
            "excerpt": "A Study of Insulin Efsitora Alfa (LY3209590) Compared With Insulin Degludec in Participants With Type 2 Diabetes Currently Treated With Basal Insulin"
          }
        ],
        "category": "Puerto Rico",
        "trial_count": 2
      },
      {
        "citations": [
          {
            "nct_id": "NCT00960661",
            "excerpt": "A Trial Comparing Two Therapies: Basal Insulin/Glargine, Exenatide and Metformin Therapy (BET) or Basal Insulin/Glargine, Bolus Insulin Lispro and Metformin Therapy (BBT) in Subjects With Type 2 Diabe"
          },
          {
            "nct_id": "NCT05352815",
            "excerpt": "A Research Study to See How Well the New Weekly Medicine IcoSema, Which is a Combination of Insulin Icodec and Semaglutide, Controls Blood Sugar Level in People With Type 2 Diabetes Compared to Weekly"
          }
        ],
        "category": "Belgium",
        "trial_count": 2
      },
      {
        "citations": [
          {
            "nct_id": "NCT03066830",
            "excerpt": "Efficacy and Safety of Sotagliflozin Versus Placebo in Participants With Type 2 Diabetes Mellitus on Background of Sulfonylurea Alone or With Metformin"
          }
        ],
        "category": "Romania",
        "trial_count": 1
      },
      {
        "citations": [
          {
            "nct_id": "NCT01495013",
            "excerpt": "A Comparison of Atorvastatin and Glimepiride Fixed Dose Combination and Atorvastatin and Glimepiride Loose Combination in the Treatment of Patients With Type 2 Diabetes Mellitus"
          }
        ],
        "category": "Russia",
        "trial_count": 1
      },
      {
        "citations": [
          {
            "nct_id": "NCT00698932",
            "excerpt": "Evaluate Efficacy and Safety of Saxagliptin in Adult Patients With Type 2 Diabetes Inadequate Glycemic Control"
          }
        ],
        "category": "Philippines",
        "trial_count": 1
      },
      {
        "citations": [
          {
            "nct_id": "NCT01894568",
            "excerpt": "A Study Comparing Insulin Peglispro With Insulin Glargine as Basal Insulin Treatment"
          }
        ],
        "category": "Japan",
        "trial_count": 1
      },
      {
        "citations": [
          {
            "nct_id": "NCT02131272",
            "excerpt": "A Trial Investigating the Efficacy and Safety of Insulin Detemir Versus Insulin NPH in Combination With Metformin and Diet/Exercise in Children and Adolescents With Type 2 Diabetes Insufficiently Cont"
          }
        ],
        "category": "Italy",
        "trial_count": 1
      },
      {
        "citations": [
          {
            "nct_id": "NCT01871415",
            "excerpt": "A Study of Aleglitazar in Combination With Metformin in Patients With Type 2 Diabetes Mellitus Who Are Inadequately Controlled With Metformin Monotherapy"
          }
        ],
        "category": "China",
        "trial_count": 1
      },
      {
        "citations": [
          {
            "nct_id": "NCT04770532",
            "excerpt": "A Research Study to Compare Two Types of Insulin, a New Weekly Insulin, Insulin Icodec and an Available Daily Insulin, Insulin Degludec, in People With Type 2 Diabetes Who Use Daily Insulin"
          }
        ],
        "category": "United States",
        "trial_count": 1
      },
      {
        "citations": [
          {
            "nct_id": "NCT00860288",
            "excerpt": "Efficacy and Long-Term Safety of Vildagliptin as Add-on Therapy to Metformin in Patients With Type 2 Diabetes"
          }
        ],
        "category": "Venezuela",
        "trial_count": 1
      }
    ]
  },
  "meta": {
    "filters_applied": {
      "condition": "diabetes",
      "phase": [
        "Phase 3"
      ],
      "country": "South Korea"
    },
    "source": "ClinicalTrials.gov v2 API",
    "query_interpretation": "Show the distribution of Phase 3 diabetes clinical trials conducted in South Korea.",
    "assumptions": [
      "Visualization type determined by rule-based fallback"
    ],
    "trial_count": 500,
    "total_matching": 819,
    "phase_filter_mode": "strict_display",
    "notes": [
      "Hybrid studies (e.g. PHASE1|PHASE2) are included when matching PHASE3 filters but displayed only under the requested phase."
    ]
  }
}
```