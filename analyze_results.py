import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load the annotated data
try:
    df = pd.read_csv("annotated_results2.csv")
except FileNotFoundError:
    print("Error: annotated_results2.csv not found.")
    exit()

if 'AI_Actually_Hallucinated' not in df.columns:
    print("⚠️ STOP: You need the 'AI_Actually_Hallucinated' column.")
    exit()

# 2. Define the Evaluation Logic
def categorize_result(row):
    ai_hallucinated = str(row['AI_Actually_Hallucinated']).strip().lower() in ['yes', 'y', 'true']
    human_verdict = str(row['human_verdict']).strip().lower()
    
    human_rejected = 'reject' in human_verdict or 'hallucination' in human_verdict
    
    if ai_hallucinated and human_rejected: return 'True Positive (Caught Lie)'
    if ai_hallucinated and not human_rejected: return 'False Negative (Blind Trust)'
    if not ai_hallucinated and not human_rejected: return 'True Negative (Correct Approval)'
    if not ai_hallucinated and human_rejected: return 'False Positive (False Alarm)'

df['Result_Category'] = df.apply(categorize_result, axis=1)

# 3. Calculate Metrics per Interface Mode
modes = df['verification_mode'].unique()

print("\n" + "="*50)
print("📊 EXPERIMENTAL RESULTS SUMMARY")
print("="*50)

results_summary = []

for mode in modes:
    mode_df = df[df['verification_mode'] == mode]
    
    TP = len(mode_df[mode_df['Result_Category'] == 'True Positive (Caught Lie)'])
    FN = len(mode_df[mode_df['Result_Category'] == 'False Negative (Blind Trust)'])
    TN = len(mode_df[mode_df['Result_Category'] == 'True Negative (Correct Approval)'])
    FP = len(mode_df[mode_df['Result_Category'] == 'False Positive (False Alarm)'])
    
    detection_rate = (TP / (TP + FN)) * 100 if (TP + FN) > 0 else 0
    total = TP + FN + TN + FP
    accuracy = ((TP + TN) / total) * 100 if total > 0 else 0
    
    results_summary.append({
        'Mode': mode,
        'Detection_Rate': detection_rate,
        'Accuracy': accuracy
    })
    
    print(f"\nMode: {mode}")
    print(f" - Detection Rate: {detection_rate:.1f}%")
    print(f" - Accuracy: {accuracy:.1f}%")

# 4. Plotting
sns.set_theme(style="whitegrid")
summary_df = pd.DataFrame(results_summary)

plt.figure(figsize=(10, 6))

# ---------- Plot 1: Detection Rate ----------
plt.subplot(1, 2, 1)
ax1 = sns.barplot(
    x='Mode', 
    y='Detection_Rate', 
    data=summary_df, 
    palette=['#e74c3c', '#2ecc71']
)

plt.title('Hallucination Detection Rate\n(Higher is better)', pad=15, fontweight='bold')
plt.ylabel('Detection Rate (%)')
plt.ylim(0, 100)

# ✅ FIX: Straight labels
plt.xticks(rotation=0, ha='center')

# ✅ ADD: Value labels on bars
for p in ax1.patches:
    height = p.get_height()
    ax1.text(
        p.get_x() + p.get_width()/2,
        height + 2,
        f'{height:.1f}%',
        ha='center',
        fontsize=10,
        fontweight='bold'
    )

# ---------- Plot 2: Accuracy ----------
plt.subplot(1, 2, 2)
ax2 = sns.barplot(
    x='Mode', 
    y='Accuracy', 
    data=summary_df, 
    palette=['#3498db', '#9b59b6']
)

plt.title('Overall Verification Accuracy', pad=15, fontweight='bold')
plt.ylabel('Accuracy (%)')
plt.ylim(0, 100)

# ✅ FIX: Straight labels
plt.xticks(rotation=0, ha='center')

# ✅ ADD: Value labels on bars
for p in ax2.patches:
    height = p.get_height()
    ax2.text(
        p.get_x() + p.get_width()/2,
        height + 2,
        f'{height:.1f}%',
        ha='center',
        fontsize=10,
        fontweight='bold'
    )

plt.tight_layout()
plt.savefig('paper_metrics_chart.png', dpi=300)
print("\n✅ Saved 'paper_metrics_chart.png'.")

plt.show()