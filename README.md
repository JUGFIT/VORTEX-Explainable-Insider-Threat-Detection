<div align="center">
    <a href="https://git.io/typing-svg">
    <img src="https://readme-typing-svg.demolab.com?font=Outfit&weight=600&size=24&letterSpacing=1px&duration=4000&pause=100&center=true&vCenter=true&width=550&lines=Solving+the+Cybersecurity+Black+Box;Actionable+Alerts+with+SHAP;Vigilant+Organizational+Risk+Tracking" alt="Typing SVG">
  </a>
  <br>
</div>

# 🛡️ Project VORTEX: Explainable Insider Threat Detection (X-ADS)

VORTEX (Vigilant Organizational Risk Tracking & Explanation) is a major academic project focused on developing a transparent and reliable system for detecting **insider threats**. It solves the "Black Box" problem of traditional anomaly detection, which suffers from a lack of accuracy and interpretability, by integrating **Explainable AI (XAI)**. The system ensures security analysts receive not just an alert, but a clear, actionable reason why the activity is suspicious.

---

## 🎯 Core Objectives

VORTEX directly addresses the high rates of false positives and the lack of clarity in existing systems.

* **Reduce False Positives (FP):** Validate anomaly alerts using contextual, human-understandable explanations.
* **Enhance Interpretability:** Utilize **SHAP** (SHapley Additive exPlanations) to attribute risk scores to specific behavioral features (e.g., unusual login time, file access count).
* **Provide Actionable Intelligence:** Transform generic security alerts into clear, evidence-based insights, allowing analysts to make faster and smarter decisions.

### 1. Clone & Setup Python Backend

```bash
# Clone the repository
git clone <Your Repository URL Here>
cd VORTEX-Explainable-Insider-Threat-Detection

# Setup and activate the virtual environment
python -m venv venv
source venv/bin/activate 

# Install Python dependencies
pip install -r requirements.txt