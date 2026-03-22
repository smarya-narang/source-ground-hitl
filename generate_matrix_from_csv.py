import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys

# 1. Load your annotated dataset
file_name = "annotated_results3.csv"
try:
    df = pd.read_csv(file_name)
except FileNotFoundError:
    print(f"🚨 Error: '{file_name}' not found. Make sure the file is in the same folder.")
    sys.exit()

# 2. Function to extract matrix values based on the Result_Category column
def extract_matrix_values(mode_name):
    # Filter by the specific experiment mode
    mode_df = df[df['verification_mode'] == mode_name]
    
    # Count occurrences of each outcome (using string matching to be safe)
    tp = len(mode_df[mode_df['Result_Category'].str.contains('True Positive', na=False)])
    fp = len(mode_df[mode_df['Result_Category'].str.contains('False Positive', na=False)])
    fn = len(mode_df[mode_df['Result_Category'].str.contains('False Negative', na=False)])
    tn = len(mode_df[mode_df['Result_Category'].str.contains('True Negative', na=False)])
    
    # Return as a 2x2 Numpy array
    return np.array([[tp, fp], [fn, tn]])

# 3. Build the matrices
blind_matrix = extract_matrix_values('Blind Mode (Control)')
grounded_matrix = extract_matrix_values('Source-Grounded (Experimental)')

# 4. Setup Labels for the heatmap
labels = np.array([["TP\n(Caught Lie)", "FP\n(False Alarm)"], 
                   ["FN\n(Blind Trust)", "TN\n(Correct)"]])

def format_annotations(matrix):
    return np.asarray([f"{val}\n{label}" for val, label in zip(matrix.flatten(), labels.flatten())]).reshape(2, 2)

blind_annot = format_annotations(blind_matrix)
grounded_annot = format_annotations(grounded_matrix)

# 5. Plotting the Heatmaps
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
sns.set_theme(style="white")

# Plot 1: Blind Mode
sns.heatmap(blind_matrix, annot=blind_annot, fmt="", cmap="Reds", cbar=False, 
            ax=axes[0], annot_kws={"size": 12, "weight": "bold"}, 
            linewidths=1, linecolor='black')
axes[0].set_title('Blind Mode (Control)', fontsize=14, fontweight='bold', pad=15)
axes[0].set_xticklabels(['AI Hallucinated', 'AI Accurate'], fontsize=11)
axes[0].set_yticklabels(['Human\nRejected', 'Human\nApproved'], fontsize=11, rotation=0)

# Plot 2: Source-Grounded Mode
sns.heatmap(grounded_matrix, annot=grounded_annot, fmt="", cmap="Greens", cbar=False, 
            ax=axes[1], annot_kws={"size": 12, "weight": "bold"}, 
            linewidths=1, linecolor='black')
axes[1].set_title('Source-Grounded (Experimental)', fontsize=14, fontweight='bold', pad=15)
axes[1].set_xticklabels(['AI Hallucinated', 'AI Accurate'], fontsize=11)
axes[1].set_yticklabels(['Human\nRejected', 'Human\nApproved'], fontsize=11, rotation=0)

# Final Formatting
plt.tight_layout()
output_filename = 'data_driven_confusion_matrix.png'
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
print(f"✅ Success! Analyzed {len(df)} total rows.")
print(f"✅ Saved '{output_filename}' at 300 DPI!")
plt.show()