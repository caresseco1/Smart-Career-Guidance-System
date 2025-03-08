import pandas as pd
import numpy as np
import re
import joblib
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.utils.class_weight import compute_class_weight
from sklearn.model_selection import train_test_split, cross_val_score

# Download necessary NLTK resources
nltk.download("stopwords")
nltk.download("punkt")

# Load dataset
df = pd.read_csv("updated_dataset.csv")

# Text Cleaning Function
def clean_text(text):
    text = text.lower()  # Convert to lowercase
    text = re.sub(r"[^a-z\s]", "", text)  # Remove special characters
    tokens = word_tokenize(text)  # Tokenize
    tokens = [word for word in tokens if word not in stopwords.words("english")]  # Remove stopwords
    return " ".join(tokens)

# Apply Cleaning to the 'Required Skills' column
df["cleaned_text"] = df["Required Skills"].apply(clean_text)

# TF-IDF Vectorization
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df["cleaned_text"])  # Use cleaned skills as input features
y = df["Job Title"]  # Use job titles as the target variable

# Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Compute Class Weights
class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
class_weight_dict = dict(zip(np.unique(y_train), class_weights))

# Train SVM Model
model = SVC(kernel="linear", class_weight=class_weight_dict)
model.fit(X_train, y_train)

# Evaluate Model with Cross Validation
cv_scores = cross_val_score(model, X_train, y_train, cv=5)  # Updated to 5 splits
print(f"Cross-validation accuracy: {np.mean(cv_scores):.2f}")

# Save Model & Vectorizer
joblib.dump(model, "model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")
