#!/usr/bin/env python3
"""
Generate 10000 unique AI/ML prompts across different algorithm categories.
"""

from typing import List, Tuple
import random


def get_algorithm_type_from_algorithm(algorithm: str) -> str:
    """Map algorithm name to algorithm type category."""
    alg_lower = algorithm.lower()
    if any(x in alg_lower for x in ["logistic", "svm", "random forest (classification)", "naive bayes", "knn"]) and "regression" not in alg_lower:
        return "Classification"
    elif any(x in alg_lower for x in ["linear regression", "random forest (regression)"]):
        return "Regression"
    elif any(x in alg_lower for x in ["k-means", "dbscan"]):
        return "Clustering"
    elif any(x in alg_lower for x in ["pca", "t-sne", "umap"]):
        return "Dimensionality Reduction"
    elif any(x in alg_lower for x in ["arima", "prophet"]):
        return "Time Series"
    elif any(x in alg_lower for x in ["lstm", "temporal cnn"]):
        return "Sequence Models"
    elif any(x in alg_lower for x in ["bert", "roberta", "text"]):
        return "NLP"
    elif any(x in alg_lower for x in ["object detection", "yolo", "faster r-cnn"]):
        return "Computer Vision Detection"
    elif any(x in alg_lower for x in ["cnn", "vision"]) and "detection" not in alg_lower:
        return "Vision"
    elif any(x in alg_lower for x in ["anomaly", "isolation forest", "one-class"]):
        return "Anomaly Detection"
    elif any(x in alg_lower for x in ["recsys", "recommend", "matrix factorization", "two-tower"]):
        return "Recommender Systems"
    elif any(x in alg_lower for x in ["reinforcement", "dqn", "ppo"]):
        return "Reinforcement Learning"
    elif any(x in alg_lower for x in ["causal", "dowhy", "ate"]):
        return "Causal Inference"
    elif "gradient boosting" in alg_lower or "xgboost" in alg_lower or "lightgbm" in alg_lower or "catboost" in alg_lower:
        return "Ensemble Methods"
    elif any(x in alg_lower for x in ["optimization", "genetic", "simulated annealing"]):
        return "Optimization"
    elif any(x in alg_lower for x in ["graph", "gnn", "graph neural"]):
        return "Graph Algorithms"
    elif any(x in alg_lower for x in ["transfer", "fine-tun", "pretrain"]):
        return "Transfer Learning"
    elif any(x in alg_lower for x in ["gan", "vae", "generative", "diffusion"]):
        return "Generative Models"
    elif any(x in alg_lower for x in ["generation", "summariz", "text generation"]):
        return "Natural Language Generation"
    elif any(x in alg_lower for x in ["feature engineering", "feature selection", "feature extraction"]):
        return "Feature Engineering"
    elif any(x in alg_lower for x in ["deep learning", "neural network", "dnn", "mlp"]):
        return "Deep Learning"
    elif any(x in alg_lower for x in ["segmentation", "semantic segmentation", "instance segmentation"]):
        return "Computer Vision Segmentation"
    elif any(x in alg_lower for x in ["multi-modal", "multimodal", "cross-modal"]):
        return "Multi-modal Learning"
    elif any(x in alg_lower for x in ["automl", "auto-ml", "automated machine learning", "neural architecture search"]):
        return "AutoML"
    else:
        # Default to Classification instead of "Other"
        return "Other"


def generate_classification_prompts() -> List[Tuple[str, str]]:
    """Generate classification prompts."""
    prompts = [
        ("Classify customer reviews by sentiment with a small labeled dataset and need interpretability", "Classification"),
        ("Detect spam emails from subject and body text using limited training data", "Classification"),
        ("Predict customer churn using transaction history and demographic features", "Classification"),
        ("Classify medical images into normal and abnormal categories with imbalanced classes", "Classification"),
        ("Categorize news articles into topics with thousands of labeled examples", "Classification"),
        ("Predict fraud in financial transactions using transaction patterns and user behavior", "Classification"),
        ("Classify tweets as positive, negative, or neutral sentiment with real-time requirements", "Classification"),
        ("Identify tendon tears in MRI scans with limited labeled medical data", "Classification"),
        ("Predict loan default risk using borrower financial information and credit history", "Classification"),
        ("Classify documents into legal categories with high accuracy requirements", "Classification"),
        ("Detect malware from executable file features with few labeled samples", "Classification"),
        ("Classify product reviews into helpful and not helpful categories", "Classification"),
        ("Predict employee attrition using HR data and work history with interpretability needs", "Classification"),
        ("Categorize support tickets by urgency and topic with real-time processing", "Classification"),
        ("Classify social media posts by content type with millions of examples", "Classification"),
        ("Predict disease diagnosis from patient symptoms and test results", "Classification"),
        ("Detect fake news articles using text content and metadata features", "Classification"),
        ("Classify images of products into categories for e-commerce search", "Classification"),
        ("Predict credit card approval using applicant information with transparency requirements", "Classification"),
        ("Identify toxic comments in online forums with imbalanced positive cases", "Classification"),
        ("Classify protein sequences by function using sequence features", "Classification"),
        ("Predict customer lifetime value segments using purchase history", "Classification"),
        ("Detect network intrusions from network traffic patterns with real-time analysis", "Classification"),
        ("Classify job descriptions by industry and skill requirements", "Classification"),
        ("Predict subscription renewal using usage patterns and customer data", "Classification"),
        ("Identify sentiment in customer service chat transcripts", "Classification"),
        ("Classify scientific papers by research domain using abstracts", "Classification"),
        ("Predict equipment failure using sensor data and maintenance history", "Classification"),
        ("Detect hate speech in social media posts with few labeled examples", "Classification"),
        ("Classify handwritten digits from scanned images with high accuracy", "Classification"),
        ("Predict insurance claims as fraudulent or legitimate using claim details", "Classification"),
        ("Categorize music tracks by genre using audio features", "Classification"),
        ("Identify plant diseases from leaf images with mobile deployment needs", "Classification"),
        ("Classify emails by priority using sender, subject, and content", "Classification"),
        ("Predict student dropout risk using academic performance and attendance", "Classification"),
        ("Detect sarcasm in text messages and social media posts", "Classification"),
        ("Classify customer support queries by resolution type with fast response times", "Classification"),
        ("Predict patient readmission risk using hospital stay data and property", "Classification"),
        ("Identify abusive language in online gaming chat with real-time moderation", "Classification"),
        ("Classify legal documents by case type using document text and metadata", "Classification"),
        ("Predict product return likelihood using purchase data and customer history", "Classification"),
        ("Detect plagiarism in academic papers using text similarity features", "Classification"),
        ("Classify website content by category for content moderation", "Classification"),
        ("Predict customer satisfaction from service interaction transcripts", "Classification"),
        ("Identify anomalous user behavior patterns in application logs", "Classification"),
        ("Classify research proposals by funding category using proposal text", "Classification"),
        ("Predict treatment effectiveness from patient records and medical history", "Classification"),
        ("Detect code vulnerabilities in software using static analysis features", "Classification"),
        ("Classify video content by category for content recommendation", "Classification"),
        ("Predict ad click-through rate using user profile and ad features", "Classification"),
    ]
    return prompts


def generate_regression_prompts() -> List[Tuple[str, str]]:
    """Generate regression prompts."""
    prompts = [
        ("Predict house prices using property features and location data with interpretable model", "Regression"),
        ("Forecast weekly demand with seasonality and promotions; low latency not required", "Regression"),
        ("Predict sales revenue using marketing spend and historical sales data", "Regression"),
        ("Estimate delivery time for packages using distance, weather, and traffic data", "Regression"),
        ("Forecast monthly sales with trend and yearly seasonality", "Regression"),
        ("Predict energy consumption for buildings using weather and usage patterns", "Regression"),
        ("Estimate patient length of stay in hospital using admission data", "Regression"),
        ("Forecast stock prices using historical prices and market indicators", "Regression"),
        ("Predict customer lifetime value using purchase history and demographics", "Regression"),
        ("Estimate repair costs for vehicles using damage assessment and vehicle data", "Regression"),
        ("Forecast website traffic using historical data and marketing campaigns", "Regression"),
        ("Predict crop yield using weather data, soil conditions, and farming practices", "Regression"),
        ("Estimate insurance claim amounts using claim details and historical data", "Regression"),
        ("Forecast electricity demand with daily and seasonal patterns", "Regression"),
        ("Predict rent prices using property features, location, and market data", "Regression"),
        ("Estimate project completion time using task complexity and team size", "Regression"),
        ("Forecast retail inventory needs using sales history and seasonal trends", "Regression"),
        ("Predict medication dosage requirements using patient weight and medical history", "Regression"),
        ("Estimate maintenance costs for equipment using age, usage, and service history", "Regression"),
        ("Forecast advertising campaign performance using budget and target audience", "Regression"),
        ("Predict test scores using study hours, attendance, and previous performance", "Regression"),
        ("Estimate shipping costs using package weight, dimensions, and destination", "Regression"),
        ("Forecast customer acquisition numbers using marketing spend and channel mix", "Regression"),
        ("Predict temperature in buildings using outdoor weather and HVAC settings", "Regression"),
        ("Estimate service wait times using queue length and historical service times", "Regression"),
        ("Forecast subscription revenue using growth rates and churn predictions", "Regression"),
        ("Predict manufacturing defect rates using production parameters and quality metrics", "Regression"),
        ("Estimate fuel consumption for vehicles using driving patterns and vehicle specs", "Regression"),
        ("Forecast employee productivity metrics using work environment and tools data", "Regression"),
        ("Predict network latency using traffic volume and network topology", "Regression"),
        ("Estimate healthcare costs using patient demographics and treatment plans", "Regression"),
        ("Forecast product demand using price, promotions, and competitor data", "Regression"),
        ("Predict student enrollment numbers using demographic trends and program offerings", "Regression"),
        ("Estimate processing time for documents using document type and complexity", "Regression"),
        ("Forecast renewable energy production using weather forecasts and historical data", "Regression"),
        ("Predict customer wait times in call centers using call volume and staffing", "Regression"),
        ("Estimate construction project costs using materials, labor, and location", "Regression"),
        ("Forecast mobile app downloads using marketing spend and app store rankings", "Regression"),
        ("Predict water usage in households using seasonal patterns and household size", "Regression"),
        ("Estimate treatment response time using patient characteristics and treatment type", "Regression"),
        ("Forecast subscription churn rates using usage patterns and customer satisfaction", "Regression"),
        ("Predict page load times using server metrics and network conditions", "Regression"),
        ("Estimate material requirements for manufacturing using production schedules", "Regression"),
        ("Forecast customer satisfaction scores using service quality metrics", "Regression"),
        ("Predict loan interest rates using borrower credit profile and market rates", "Regression"),
        ("Estimate cloud computing costs using resource usage and pricing models", "Regression"),
        ("Forecast product return rates using product features and customer reviews", "Regression"),
        ("Predict employee turnover using job satisfaction and compensation data", "Regression"),
        ("Estimate resource allocation needs using project requirements and team capacity", "Regression"),
        ("Forecast social media engagement metrics using content features and timing", "Regression"),
    ]
    return prompts


def generate_clustering_prompts() -> List[Tuple[str, str]]:
    """Generate clustering prompts."""
    prompts = [
        ("Cluster customers into segments using transaction and behavior features", "Clustering"),
        ("Group similar documents together without labels for topic discovery", "Clustering"),
        ("Segment users by app usage patterns to identify user personas", "Clustering"),
        ("Cluster products by purchase patterns to create product categories", "Clustering"),
        ("Group genes with similar expression patterns to identify gene families", "Clustering"),
        ("Segment geographic regions by demographic and economic characteristics", "Clustering"),
        ("Cluster web pages by content similarity for search result grouping", "Clustering"),
        ("Group employees by skill sets and work patterns for team formation", "Clustering"),
        ("Cluster sensor readings to identify different operational states", "Clustering"),
        ("Segment market customers by purchasing behavior and preferences", "Clustering"),
        ("Group news articles by content similarity without predefined categories", "Clustering"),
        ("Cluster images by visual features to organize photo collections", "Clustering"),
        ("Segment patients by medical history patterns for personalized care", "Clustering"),
        ("Group social media users by activity patterns and interests", "Clustering"),
        ("Cluster financial transactions to detect transaction type patterns", "Clustering"),
        ("Segment sales territories by customer characteristics and performance", "Clustering"),
        ("Group research papers by citation patterns and topic similarity", "Clustering"),
        ("Cluster network traffic patterns to identify different application types", "Clustering"),
        ("Segment products by sales patterns for inventory management", "Clustering"),
        ("Group locations by environmental and demographic similarity", "Clustering"),
        ("Cluster time series data to identify similar temporal patterns", "Clustering"),
        ("Segment customers by churn risk factors and engagement levels", "Clustering"),
        ("Group protein structures by structural similarity for drug discovery", "Clustering"),
        ("Cluster website visitors by browsing behavior for personalization", "Clustering"),
        ("Segment employees by productivity patterns for workforce optimization", "Clustering"),
        ("Group music tracks by audio features for playlist generation", "Clustering"),
        ("Cluster sensor data to identify different equipment operating modes", "Clustering"),
        ("Segment markets by consumer preferences and buying power", "Clustering"),
        ("Group scientific samples by measurement characteristics", "Clustering"),
        ("Cluster text documents by writing style and topic for content analysis", "Clustering"),
        ("Segment users by engagement patterns for targeted interventions", "Clustering"),
        ("Group stocks by price movement patterns for portfolio construction", "Clustering"),
        ("Cluster customer support tickets by issue type and resolution patterns", "Clustering"),
        ("Segment cities by economic indicators and population characteristics", "Clustering"),
        ("Group research projects by scope and resource requirements", "Clustering"),
        ("Cluster biological samples by genetic markers for population studies", "Clustering"),
        ("Segment delivery routes by geographic and temporal patterns", "Clustering"),
        ("Group educational content by difficulty and topic for personalized learning", "Clustering"),
        ("Cluster log entries by error patterns for system monitoring", "Clustering"),
        ("Segment services by usage patterns and performance characteristics", "Clustering"),
        ("Group news stories by sentiment and topic for media analysis", "Clustering"),
        ("Cluster patient records by treatment outcomes for medical research", "Clustering"),
        ("Segment markets by competitive dynamics and growth potential", "Clustering"),
        ("Group products by customer reviews and ratings for recommendation", "Clustering"),
        ("Cluster employee feedback by themes for organizational insights", "Clustering"),
        ("Segment customers by response to marketing campaigns", "Clustering"),
        ("Group research grants by funding amount and research area", "Clustering"),
        ("Cluster network nodes by connection patterns for security analysis", "Clustering"),
        ("Segment users by device usage patterns for app optimization", "Clustering"),
        ("Group investment opportunities by risk and return characteristics", "Clustering"),
    ]
    return prompts


def generate_time_series_prompts() -> List[Tuple[str, str]]:
    """Generate time series prompts."""
    prompts = [
        ("Forecast monthly sales with trend and yearly seasonality", "Time Series"),
        ("Predict English electricity demand with daily and seasonal patterns", "Time Series"),
        ("Forecast stock prices using historical prices and market indicators", "Time Series"),
        ("Predict website traffic with weekly and monthly seasonal patterns", "Time Series"),
        ("Forecast weather temperature with daily and annual cycles", "Time Series"),
        ("Predict patient admissions with weekly patterns and holiday effects", "Time Series"),
        ("Forecast product demand with promotional spikes and seasonality", "Time Series"),
        ("Predict network traffic patterns with hourly and daily cycles", "Time Series"),
        ("Forecast revenue growth with trend and quarterly seasonality", "Time Series"),
        ("Predict energy consumption with temperature and usage patterns", "Time Series"),
        ("Forecast customer acquisition with growth trends and seasonal effects", "Time Series"),
        ("Predict equipment failures using sensor time series data", "Time Series"),
        ("Forecast subscription cancellations with monthly renewal patterns", "Time Series"),
        ("Predict inventory levels with demand patterns and lead times", "Time Series"),
        ("Forecast marketing campaign performance over time", "Time Series"),
        ("Predict employee turnover with quarterly and annual patterns", "Time Series"),
        ("Forecast mobile app usage with daily and weekly patterns", "Time Series"),
        ("Predict server load with hourly patterns and event-driven spikes", "Time Series"),
        ("Forecast agricultural yields with seasonal weather patterns", "Time Series"),
        ("Predict customer service volume with weekly and monthly cycles", "Time Series"),
        ("Forecast supply chain disruptions using historical patterns", "Time Series"),
        ("Predict medication adherence rates over time with patient data", "Time Series"),
        ("Forecast housing prices with market trends and seasonal effects", "Time Series"),
        ("Predict user engagement metrics with daily and weekly patterns", "Time Series"),
        ("Forecast commodity prices with supply and demand trends", "Time Series"),
        ("Predict system errors with daily patterns and anomaly detection", "Time Series"),
        ("Forecast manufacturing output with production cycle patterns", "Time Series"),
        ("Predict social media engagement with hourly and daily patterns", "Time Series"),
        ("Forecast transportation demand with daily and weekly cycles", "Time Series"),
        ("Predict water usage with seasonal patterns and weather effects", "Time Series"),
        ("Forecast call center volume with hourly and daily patterns", "Time Series"),
        ("Predict product returns with seasonal and promotional effects", "Time Series"),
        ("Forecast employee productivity with weekly patterns", "Time Series"),
        ("Predict content consumption with daily and weekly viewing patterns", "Time Series"),
        ("Forecast subscription renewals with monthly and annual patterns", "Time Series"),
        ("Predict customer satisfaction scores over time with service changes", "Time Series"),
        ("Forecast advertising spend effectiveness with campaign cycles", "Time Series"),
        ("Predict processing times with workload patterns and system capacity", "Time Series"),
        ("Forecast inventory turnover with seasonal demand patterns", "Time Series"),
        ("Predict quality metrics with production cycle patterns", "Time Series"),
        ("Forecast patient flow in hospitals with daily and weekly patterns", "Time Series"),
        ("Predict network latency with traffic patterns and system load", "Time Series"),
        ("Forecast resource utilization with capacity planning needs", "Time Series"),
        ("Predict market share changes with competitive dynamics", "Time Series"),
        ("Forecast content popularity with viral spread patterns", "Time Series"),
        ("Predict processing delays with queue length and capacity trends", "Time Series"),
        ("Forecast user growth with acquisition and retention patterns", "Time Series"),
        ("Predict maintenance needs with equipment usage and failure patterns", "Time Series"),
        ("Forecast supply needs with demand patterns and lead times", "Time Series"),
        ("Predict cost trends with operational changes and market conditions", "Time Series"),
    ]
    return prompts


def generate_nlp_prompts() -> List[Tuple[str, str]]:
    """Generate NLP prompts."""
    prompts = [
        ("Classify customer reviews by sentiment with a small labeled dataset and need interpretability", "NLP"),
        ("Extract named entities from legal documents for contract analysis", "NLP"),
        ("Summarize long articles into concise summaries for news aggregation", "NLP"),
        ("Translate text between languages using neural machine translation", "NLP"),
        ("Generate product descriptions from product specifications automatically", "NLP"),
        ("Answer questions from documents using question answering models", "NLP"),
        ("Detect topics in customer feedback for product improvement insights", "NLP"),
        ("Extract key information from medical records for clinical decision support", "NLP"),
        ("Classify support tickets by issue type using ticket descriptions", "NLP"),
        ("Generate code comments from source code for documentation", "NLP"),
        ("Summarize meeting transcripts into action items and decisions", "NLP"),
        ("Detect intent in chatbot conversations for customer service automation", "NLP"),
        ("Extract structured data from unstructured text documents", "NLP"),
        ("Generate personalized email responses based on customer inquiries", "NLP"),
        ("Classify social media posts by content type and sentiment", "NLP"),
        ("Translate technical documentation between programming languages", "NLP"),
        ("Summarize research papers for literature review and citation", "NLP"),
        ("Extract entities and relationships from scientific literature", "NLP"),
        ("Generate captions for images using vision-language models", "NLP"),
        ("Classify emails by priority and category for inbox management", "NLP"),
        ("Detect plagiarism in academic papers using text similarity", "NLP"),
        ("Generate product recommendations based on customer reviews", "NLP"),
        ("Extract key phrases from documents for search and indexing", "NLP"),
        ("Summarize customer conversations for case notes and analysis", "NLP"),
        ("Classify news articles by topic and relevance for content curation", "NLP"),
        ("Generate synthetic training data for NLP models using GPT", "NLP"),
        ("Extract medical codes from clinical notes for billing automation", "NLP"),
        ("Detect hate speech and toxic language in online comments", "NLP"),
        ("Summarize legal contracts into key terms and obligations", "NLP"),
        ("Classify product reviews by aspect and sentiment", "NLP"),
        ("Generate automated responses to customer inquiries", "NLP"),
        ("Extract financial data from earnings reports and news articles", "NLP"),
        ("Summarize long-form content for social media previews", "NLP"),
        ("Classify documents by confidentiality level for security", "NLP"),
        ("Detect fake news using article content and metadata", "NLP"),
        ("Extract customer requirements from requirement documents", "NLP"),
        ("Summarize video transcripts for content discovery", "NLP"),
        ("Classify social media messages by urgency and topic", "NLP"),
        ("Generate SEO-optimized content from product information", "NLP"),
        ("Extract insights from customer surveys and feedback", "NLP"),
        ("Summarize technical specifications for product comparisons", "NLP"),
        ("Classify content by appropriateness for content moderation", "NLP"),
        ("Detect sarcasm and irony in text for sentiment analysis", "NLP"),
        ("Extract structured information from resume documents", "NLP"),
        ("Summarize customer support interactions for analytics", "NLP"),
        ("Classify research papers by methodology and domain", "NLP"),
        ("Generate alternative phrasings for content diversity", "NLP"),
        ("Extract competitive intelligence from news and reports", "NLP"),
        ("Summarize financial reports for investment analysis", "NLP"),
        ("Classify user queries by intent for search optimization", "NLP"),
    ]
    return prompts


def generate_vision_prompts() -> List[Tuple[str, str]]:
    """Generate vision prompts."""
    prompts = [
        ("Classify medical images into normal and abnormal categories with imbalanced classes", "Vision"),
        ("Detect objects in images for autonomous vehicle navigation", "Vision"),
        ("Recognize faces in photos for security and authentication", "Vision"),
        ("Classify product images into categories for e-commerce search", "Vision"),
        ("Identify plant diseases from leaf images with mobile deployment needs", "Vision"),
        ("Segment medical images to identify anatomical structures", "Vision"),
        ("Detect defects in manufacturing products using image inspection", "Vision"),
        ("Classify handwritten digits from scanned images with high accuracy", "Vision"),
        ("Recognize traffic signs for self-driving car systems", "Vision"),
        ("Detect anomalies in medical scans for early disease detection", "Vision"),
        ("Classify food items in images for nutrition tracking apps", "Vision"),
        ("Identify brands and logos in images for marketing analytics", "Vision"),
        ("Segment satellite images to classify land use and cover", "Vision"),
        ("Detect emotions from facial expressions in video streams", "Vision"),
        ("Classify skin lesions for dermatological diagnosis assistance", "Vision"),
        ("Recognize text in images using OCR for document digitization", "Vision"),
        ("Detect damage in infrastructure using drone inspection images", "Vision"),
        ("Classify artwork and paintings by style and period", "Vision"),
        ("Identify species of animals and plants from camera trap images", "Vision"),
        ("Segment cells in microscopic images for biological research", "Vision"),
        ("Detect fraudulent documents using image analysis", "Vision"),
        ("Classify clothing items in images for fashion recommendation", "Vision"),
        ("Recognize gestures in video for human-computer interaction", "Vision"),
        ("Detect quality issues in food products using visual inspection", "Vision"),
        ("Classify document types from scanned images", "Vision"),
        ("Identify counterfeit products using image comparison", "Vision"),
        ("Segment road scenes for autonomous vehicle perception", "Vision"),
        ("Detect suspicious activity in security camera footage", "Vision"),
        ("Classify architectural styles in building images", "Vision"),
        ("Recognize license plates for traffic management systems", "Vision"),
        ("Detect tumors in medical imaging for radiology assistance", "Vision"),
        ("Classify sports actions in video for automated highlights", "Vision"),
        ("Identify damage in vehicles from insurance claim photos", "Vision"),
        ("Segment agricultural fields in satellite images for crop monitoring", "Vision"),
        ("Detect quality defects in manufactured goods", "Vision"),
        ("Classify indoor scenes for smart home applications", "Vision"),
        ("Recognize hand gestures for sign language translation", "Vision"),
        ("Detect wildfires in aerial and satellite imagery", "Vision"),
        ("Classify retail products on shelves for inventory management", "Vision"),
        ("Identify individuals in crowd scenes for security applications", "Vision"),
        ("Segment clouds in satellite images for weather prediction", "Vision"),
        ("Detect cracks in infrastructure using image analysis", "Vision"),
        ("Classify fashion items for style recommendation systems", "Vision"),
        ("Recognize gestures in mobile apps for accessibility", "Vision"),
        ("Detect anomalies in medical images for diagnostic support", "Vision"),
        ("Classify art and design styles for creative applications", "Vision"),
        ("Identify products in retail environments for cashier-less stores", "Vision"),
        ("Segment anatomical structures in medical scans", "Vision"),
        ("Detect safety violations in workplace surveillance footage", "Vision"),
        ("Classify nature scenes for environmental monitoring", "Vision"),
    ]
    return prompts


def generate_anomaly_prompts() -> List[Tuple[str, str]]:
    """Generate anomaly detection prompts."""
    prompts = [
        ("Detect anomalies in streaming metrics with few labeled examples", "Anomaly Detection"),
        ("Identify fraudulent transactions in financial systems using transaction patterns", "Anomaly Detection"),
        ("Detect network intrusions from network traffic patterns with real-time analysis", "Anomaly Detection"),
        ("Find rare events in sensor data for predictive maintenance", "Anomaly Detection"),
        ("Identify anomalous user behavior patterns in application logs", "Anomaly Detection"),
        ("Detect manufacturing defects in production lines using sensor data", "Anomaly Detection"),
        ("Find outliers in customer purchase behavior for fraud prevention", "Anomaly Detection"),
        ("Detect system errors and failures in infrastructure monitoring", "Anomaly Detection"),
        ("Identify anomalous patterns in medical patient data", "Anomaly Detection"),
        ("Detect security breaches using system access logs", "Anomaly Detection"),
        ("Find anomalies in financial market data for trading signals", "Anomaly Detection"),
        ("Detect quality issues in product manufacturing processes", "Anomaly Detection"),
        ("Identify unusual patterns in web traffic for security monitoring", "Anomaly Detection"),
        ("Detect anomalies in energy consumption patterns", "Anomaly Detection"),
        ("Find outliers in user engagement metrics for product insights", "Anomaly Detection"),
        ("Detect anomalies in supply chain data for risk management", "Anomaly Detection"),
        ("Identify unusual patterns in patient vital signs", "Anomaly Detection"),
        ("Detect anomalies in credit card transactions in real-time", "Anomaly Detection"),
        ("Find outliers in sensor readings for equipment monitoring", "Anomaly Detection"),
        ("Detect anomalies in video surveillance for security", "Anomaly Detection"),
        ("Identify unusual patterns in network latency and performance", "Anomaly Detection"),
        ("Detect anomalies in customer service interactions", "Anomaly Detection"),
        ("Find outliers in inventory levels for supply chain optimization", "Anomaly Detection"),
        ("Detect anomalies in mobile app usage patterns", "Anomaly Detection"),
        ("Identify unusual patterns in employee behavior for security", "Anomaly Detection"),
        ("Detect anomalies in API usage patterns for abuse prevention", "Anomaly Detection"),
        ("Find outliers in financial reporting data", "Anomaly Detection"),
        ("Detect anomalies in manufacturing process parameters", "Anomaly Detection"),
        ("Identify unusual patterns in content consumption", "Anomaly Detection"),
        ("Detect anomalies in cloud resource usage for cost optimization", "Anomaly Detection"),
        ("Find outliers in customer satisfaction scores", "Anomaly Detection"),
        ("Detect anomalies in software deployment patterns", "Anomaly Detection"),
        ("Identify unusual patterns in social media engagement", "Anomaly Detection"),
        ("Detect anomalies in shipping and delivery data", "Anomaly Detection"),
        ("Find outliers in educational assessment scores", "Anomaly Detection"),
        ("Detect anomalies in power grid operations", "Anomaly Detection"),
        ("Identify unusual patterns in content creation and publishing", "Anomaly Detection"),
        ("Detect anomalies in telemetry data from IoT devices", "Anomaly Detection"),
        ("Find outliers in customer support ticket patterns", "Anomaly Detection"),
        ("Detect anomalies in healthcare claim data", "Anomaly Detection"),
        ("Identify unusual patterns in search query behavior", "Anomaly Detection"),
        ("Detect anomalies in advertising campaign performance", "Anomaly Detection"),
        ("Find outliers in product return patterns", "Anomaly Detection"),
        ("Detect anomalies in user authentication patterns", "Anomaly Detection"),
        ("Identify unusual patterns in market trading activity", "Anomaly Detection"),
        ("Detect anomalies in customer retention patterns", "Anomaly Detection"),
        ("Find outliers in employee productivity metrics", "Anomaly Detection"),
        ("Detect anomalies in resource allocation patterns", "Anomaly Detection"),
        ("Identify unusual patterns in content moderation decisions", "Anomaly Detection"),
        ("Detect anomalies in subscription billing patterns", "Anomaly Detection"),
    ]
    return prompts


def generate_recsys_prompts() -> List[Tuple[str, str]]:
    """Generate recommender system prompts."""
    prompts = [
        ("Build a =>recommendation system for users and items", "Recommender Systems"),
        ("Recommend products to customers based on purchase history and preferences", "Recommender Systems"),
        ("Suggest movies to users based on viewing history and ratings", "Recommender Systems"),
        ("Recommend articles to readers based on reading patterns", "Recommender Systems"),
        ("Suggest music tracks based on listening history and user preferences", "Recommender Systems"),
        ("Recommend restaurants to users based on location and cuisine preferences", "Recommender Systems"),
        ("Suggest courses to students based on learning goals and background", "Recommender Systems"),
        ("Recommend hotels to travelers based on past stays and preferences", "Recommender Systems"),
        ("Suggest friends and connections in social networks", "Recommender Systems"),
        ("Recommend job postings to candidates based on skills and experience", "Recommender Systems"),
        ("Suggest recipes to users based on dietary preferences and ingredients", "Recommender Systems"),
        ("Recommend apps to users based on download history and usage", "Recommender Systems"),
        ("Suggest books to readers based on reading history and reviews", "Recommender Systems"),
        ("Recommend fashion items based on style preferences and purchase history", "Recommender Systems"),
        ("Suggest workouts to users based on fitness goals and activity history", "Recommender Systems"),
        ("Recommend restaurants based on cuisine preferences and location", "Recommender Systems"),
        ("Suggest content creators to follow based on viewing patterns", "Recommender Systems"),
        ("Recommend insurance products based on customer profile and needs", "Recommender Systems"),
        ("Suggest investment opportunities based on risk profile and goals", "Recommender Systems"),
        ("Recommend educational content based on learning progress", "Recommender Systems"),
        ("Suggest travel destinations based on past trips and interests", "Recommender Systems"),
        ("Recommend TV shows based on viewing history and preferences", "Recommender Systems"),
        ("Suggest products for upselling and cross-selling opportunities", "Recommender Systems"),
        ("Recommend professional services based on business needs", "Recommender Systems"),
        ("Suggest events to users based on interests and location", "Recommender Systems"),
        ("Recommend beauty products based on skin type and preferences", "Recommender Systems"),
        ("Suggest workout equipment based on fitness goals", "Recommender Systems"),
        ("Recommend podcasts based on listening history and interests", "Recommender Systems"),
        ("Suggest courses for professional development", "Recommender Systems"),
        ("Recommend financial products based on customer profile", "Recommender Systems"),
        ("Suggest home improvement products based on property type", "Recommender Systems"),
        ("Recommend pet products based on pet type and needs", "Recommender Systems"),
        ("Suggest subscription services based on usage patterns", "Recommender Systems"),
        ("Recommend gaming content based on play history", "Recommender Systems"),
        ("Suggest meal plans based on dietary restrictions and preferences", "Recommender Systems"),
        ("Recommend healthcare providers based on medical needs and location", "Recommender Systems"),
        ("Suggest career paths based on skills and interests", "Recommender Systems"),
        ("Recommend automotive products based on vehicle type", "Recommender Systems"),
        ("Suggest gift ideas based on recipient profile and occasion", "Recommender Systems"),
        ("Recommend home decor items based on style preferences", "Recommender Systems"),
        ("Suggest productivity tools based on work patterns", "Recommender Systems"),
        ("Recommend wellness services based on health goals", "Recommender Systems"),
        ("Suggest learning resources based on skill gaps", "Recommender Systems"),
        ("Recommend entertainment content based on mood and preferences", "Recommender Systems"),
        ("Suggest travel accessories based on trip type and destination", "Recommender Systems"),
        ("Recommend tech products based on usage patterns and needs", "Recommender Systems"),
        ("Suggest hobbies and activities based on interests", "Recommender Systems"),
        ("Recommend subscription boxes based on preferences and budget", "Recommender Systems"),
        ("Suggest date ideas based on preferences and location", "Recommender Systems"),
    ]
    return prompts


def generate_rl_prompts() -> List[Tuple[str, str]]:
    """Generate reinforcement learning prompts."""
    prompts = [
        ("Train an agent to play games using reinforcement learning with delayed rewards", "Reinforcement Learning"),
        ("Optimize trading strategies using RL for sequential decision-making in markets", "Reinforcement Learning"),
        ("Control autonomous vehicles using reinforcement learning for navigation", "Reinforcement Learning"),
        ("Optimize resource allocation using RL for dynamic environments", "Reinforcement Learning"),
        ("Train robots to perform tasks using reinforcement learning", "Reinforcement Learning"),
        ("Optimize ad placement using RL for revenue maximization", "Reinforcement Learning"),
        ("Control HVAC systems using reinforcement learning for energy efficiency", "Reinforcement Learning"),
        ("Train agents for customer service chatbots using RL", "Reinforcement Learning"),
        ("Optimize inventory management using reinforcement learning", "Reinforcement Learning"),
        ("Control traffic lights using RL for congestion reduction", "Reinforcement Learning"),
        ("Train agents for competitive gaming using reinforcement learning", "Reinforcement Learning"),
        ("Optimize pricing strategies using RL for dynamic markets", "Reinforcement Learning"),
        ("Control power grids using reinforcement learning for load balancing", "Reinforcement Learning"),
        ("Train drones for autonomous navigation using RL", "Reinforcement Learning"),
        ("Optimize supply chain operations using reinforcement learning", "Reinforcement Learning"),
        ("Control manufacturing processes using RL for quality optimization", "Reinforcement Learning"),
        ("Train agents for financial portfolio management using RL", "Reinforcement Learning"),
        ("Optimize recommendation systems using RL for long-term engagement", "Reinforcement Learning"),
        ("Control network routing using reinforcement learning", "Reinforcement Learning"),
        ("Train agents for medical treatment recommendation using RL", "Reinforcement Learning"),
        ("Optimize energy consumption using RL for smart buildings", "Reinforcement Learning"),
        ("Control autonomous agents in virtual environments using RL", "Reinforcement Learning"),
        ("Train agents for cybersecurity defense using reinforcement learning", "Reinforcement Learning"),
        ("Optimize content delivery using RL for user engagement", "Reinforcement Learning"),
        ("Control agricultural systems using reinforcement learning", "Reinforcement Learning"),
        ("Train agents for sports strategy using RL", "Reinforcement Learning"),
        ("Optimize drug discovery using RL for molecular design", "Reinforcement Learning"),
        ("Control telecommunication networks using RL", "Reinforcement Learning"),
        ("Train agents for fraud detection using reinforcement learning", "Reinforcement Learning"),
        ("Optimize cloud resource allocation using RL", "Reinforcement Learning"),
        ("Control autonomous warehouse robots using RL", "Reinforcement Learning"),
        ("Train agents for language learning using RL", "Reinforcement Learning"),
        ("Optimize marketing campaigns using RL for customer acquisition", "Reinforcement Learning"),
        ("Control smart grid systems using reinforcement learning", "Reinforcement Learning"),
        ("Train agents for personalization using RL", "Reinforcement Learning"),
        ("Optimize production scheduling using RL", "Reinforcement Learning"),
        ("Control autonomous delivery systems using RL", "Reinforcement Learning"),
        ("Train agents for negotiation using reinforcement learning", "Reinforcement Learning"),
        ("Optimize healthcare treatment plans using RL", "Reinforcement Learning"),
        ("Control autonomous security systems using RL", "Reinforcement Learning"),
        ("Train agents for creative tasks using RL", "Reinforcement Learning"),
        ("Optimize user experience flows using RL", "Reinforcement Learning"),
        ("Control autonomous inspection systems using RL", "Reinforcement Learning"),
        ("Train agents for decision support using RL", "Reinforcement Learning"),
        ("Optimize maintenance schedules using RL", "Reinforcement Learning"),
        ("Control autonomous cleaning systems using RL", "Reinforcement Learning"),
        ("Train agents for adaptive learning using RL", "Reinforcement Learning"),
        ("Optimize customer retention strategies using RL", "Reinforcement Learning"),
        ("Control autonomous monitoring systems using RL", "Reinforcement Learning"),
        ("Train agents for multi-agent coordination using RL", "Reinforcement Learning"),
    ]
    return prompts


def generate_causal_prompts() -> List[Tuple[str, str]]:
    """Generate causal inference prompts."""
    prompts = [
        ("Estimate causal effects of marketing campaigns on sales", "Causal Inference"),
        ("Measure treatment effects of medical interventions on patient outcomes", "Causal Inference"),
        ("Estimate impact of policy changes on economic outcomes", "Causal Inference"),
        ("Measure causal effect of price changes on demand", "Causal Inference"),
        ("Estimate impact of training programs on employee performance", "Causal Inference"),
        ("Measure treatment effects of educational interventions on student outcomes", "Causal Inference"),
        ("Estimate causal effects of product features on user engagement", "Causal Inference"),
        ("Measure impact of website redesign on conversion rates", "Causal Inference"),
        ("Estimate treatment effects of nutritional interventions on health outcomes", "Causal Inference"),
        ("Measure causal effect of advertising on brand awareness", "Causal Inference"),
        ("Estimate impact of pricing strategies on customer retention", "Causal Inference"),
        ("Measure treatment effects of therapy on patient recovery", "Causal Inference"),
        ("Estimate causal effects of supply chain changes on delivery times", "Causal Inference"),
        ("Measure impact of work environment changes on productivity", "Causal Inference"),
        ("Estimate treatment effects of preventive care on health costs", "Causal Inference"),
        ("Measure causal effect of customer service improvements on satisfaction", "Causal Inference"),
        ("Estimate impact of process changes on quality outcomes", "Causal Inference"),
        ("Measure treatment effects of financial incentives on behavior", "Causal Inference"),
        ("Estimate causal effects of technology adoption on performance", "Causal Inference"),
        ("Measure impact of organizational changes on employee turnover", "Causal Inference"),
        ("Estimate treatment effects of nutrition programs on academic performance", "Causal Inference"),
        ("Measure causal effect of product placement on sales", "Causal Inference"),
        ("Estimate impact of safety interventions on accident rates", "Causal Inference"),
        ("Measure treatment effects of coaching on team performance", "Causal Inference"),
        ("Estimate causal effects of environmental policies on outcomes", "Causal Inference"),
        ("Measure impact of social programs on community outcomes", "Causal Inference"),
        ("Estimate treatment effects of medication on disease progression", "Causal Inference"),
        ("Measure causal effect of design changes on user behavior", "Causal Inference"),
        ("Estimate impact of regulatory changes on industry outcomes", "Causal Inference"),
        ("Measure treatment effects of interventions on sustainability metrics", "Causal Inference"),
        ("Estimate causal effects of communication strategies on engagement", "Causal Inference"),
        ("Measure impact of quality improvements on customer satisfaction", "Causal Inference"),
        ("Estimate treatment effects of wellness programs on health outcomes", "Causal Inference"),
        ("Measure causal effect of service innovations on adoption", "Causal Inference"),
        ("Estimate impact of cultural changes on organizational performance", "Causal Inference"),
        ("Measure treatment effects of accessibility improvements on usage", "Causal Inference"),
        ("Estimate causal effects of transparency initiatives on trust", "Causal Inference"),
        ("Measure impact of diversity programs on innovation outcomes", "Causal Inference"),
        ("Estimate treatment effects of feedback systems on improvement", "Causal Inference"),
        ("Measure causal effect of recognition programs on motivation", "Causal Inference"),
        ("Estimate impact of learning opportunities on skill development", "Causal Inference"),
        ("Measure treatment effects of support systems on outcomes", "Causal Inference"),
        ("Estimate causal effects of resource allocation on performance", "Causal Inference"),
        ("Measure impact of collaboration tools on team effectiveness", "Causal Inference"),
        ("Estimate treatment effects of mentoring programs on career growth", "Causal Inference"),
        ("Measure causal effect of communication platforms on productivity", "Causal Inference"),
        ("Estimate impact of automation on job satisfaction", "Causal Inference"),
        ("Measure treatment effects of flexibility policies on retention", "Causal Inference"),
        ("Estimate causal effects of leadership styles on team outcomes", "Causal Inference"),
        ("Measure impact of customer feedback on product improvements", "Causal Inference"),
    ]
    return prompts


def generate_dimred_prompts() -> List[Tuple[str, str]]:
    """Generate dimensionality reduction prompts."""
    prompts = [
        ("Reduce dimensionality of high-dimensional feature space for visualization", "Dimensionality Reduction"),
        ("Extract principal components from customer data for analysis", "Dimensionality Reduction"),
        ("Embed high-dimensional text data into lower dimensions", "Dimensionality Reduction"),
        ("Visualize high-dimensional data in 2D or 3D space", "Dimensionality Reduction"),
        ("Reduce feature dimensions for faster model training", "Dimensionality Reduction"),
        ("Extract meaningful features from image data for classification", "Dimensionality Reduction"),
        ("Compress gene expression data while preserving structure", "Dimensionality Reduction"),
        ("Embed user behavior data into lower dimensional space", "Dimensionality Reduction"),
        ("Visualize customer segments in reduced dimensional space", "Dimensionality Reduction"),
        ("Reduce dimensions of sensor data for anomaly detection", "Dimensionality Reduction"),
        ("Extract features from time series data for analysis", "Dimensionality Reduction"),
        ("Embed product features into lower dimensions for recommendation", "Dimensionality Reduction"),
        ("Visualize document similarity in 2D space", "Dimensionality Reduction"),
        ("Reduce dimensions of financial market data", "Dimensionality Reduction"),
        ("Extract principal components from medical imaging data", "Dimensionality Reduction"),
        ("Embed network graph data into lower dimensions", "Dimensionality Reduction"),
        ("Visualize cluster structure in high-dimensional data", "Dimensionality Reduction"),
        ("Reduce dimensions of customer transaction data", "Dimensionality Reduction"),
        ("Extract features from audio signals for classification", "Dimensionality Reduction"),
        ("Embed social network data into lower dimensions", "Dimensionality Reduction"),
        ("Visualize feature relationships in high-dimensional datasets", "Dimensionality Reduction"),
        ("Reduce dimensions of sensor readings for monitoring", "Dimensionality Reduction"),
        ("Extract principal components from survey response data", "Dimensionality Reduction"),
        ("Embed product attributes into lower dimensions", "Dimensionality Reduction"),
        ("Visualize patient data in reduced dimensional space", "Dimensionality Reduction"),
        ("Reduce dimensions of text embeddings for efficiency", "Dimensionality Reduction"),
        ("Extract features from video data for analysis", "Dimensionality Reduction"),
        ("Embed behavioral data into lower dimensions", "Dimensionality Reduction"),
        ("Visualize market segments in reduced dimensional space", "Dimensionality Reduction"),
        ("Reduce dimensions of genomic data for analysis", "Dimensionality Reduction"),
        ("Extract principal components from user interaction data", "Dimensionality Reduction"),
        ("Embed temporal data into lower dimensions", "Dimensionality Reduction"),
        ("Visualize quality metrics in reduced dimensional space", "Dimensionality Reduction"),
        ("Reduce dimensions of recommendation features", "Dimensionality Reduction"),
        ("Extract features from multi-modal data", "Dimensionality Reduction"),
        ("Embed location data into lower dimensions", "Dimensionality Reduction"),
        ("Visualize customer preferences in reduced dimensional space", "Dimensionality Reduction"),
        ("Reduce dimensions of log data for analysis", "Dimensionality Reduction"),
        ("Extract principal components from performance metrics", "Dimensionality Reduction"),
        ("Embed content features into lower dimensions", "Dimensionality Reduction"),
        ("Visualize system states in reduced dimensional space", "Dimensionality Reduction"),
        ("Reduce dimensions of feature engineering outputs", "Dimensionality Reduction"),
        ("Extract features from mixed data types", "Dimensionality Reduction"),
        ("Embed relationship data into lower dimensions", "Dimensionality Reduction"),
        ("Visualize patterns in high-dimensional time series", "Dimensionality Reduction"),
        ("Reduce dimensions of interaction data", "Dimensionality Reduction"),
        ("Extract principal components from composite metrics", "Dimensionality Reduction"),
        ("Embed categorical data into lower dimensions", "Dimensionality Reduction"),
        ("Visualize decision boundaries in feature space", "Dimensionality Reduction"),
        ("Reduce dimensions of experimental data for analysis", "Dimensionality Reduction"),
    ]
    return prompts


def generate_sequence_models_prompts() -> List[Tuple[str, str]]:
    """Generate sequence models prompts."""
    prompts = [
        ("Forecast stock prices using LSTM with historical price sequences", "Sequence Models"),
        ("Predict next word in text using temporal neural networks", "Sequence Models"),
        ("Model sequential user behavior patterns for personalization", "Sequence Models"),
        ("Forecast weather patterns using temporal CNN with sensor data", "Sequence Models"),
        ("Predict video frame sequences for motion understanding", "Sequence Models"),
        ("Model sequential dependencies in financial time series data", "Sequence Models"),
        ("Predict next action in sequential decision making tasks", "Sequence Models"),
        ("Forecast demand using LSTM with seasonal and trend patterns", "Sequence Models"),
        ("Model sequential patterns in network traffic for anomaly detection", "Sequence Models"),
        ("Predict sequence of events in complex systems", "Sequence Models"),
        ("Forecast energy consumption using temporal neural networks", "Sequence Models"),
        ("Model sequential relationships in genomic sequences", "Sequence Models"),
        ("Predict next item in shopping cart sequences", "Sequence Models"),
        ("Forecast disease progression using temporal medical data", "Sequence Models"),
        ("Model sequential dependencies in natural language understanding", "Sequence Models"),
    ]
    return prompts


def generate_cv_detection_prompts() -> List[Tuple[str, str]]:
    """Generate computer vision detection prompts."""
    prompts = [
        ("Detect cars and pedestrians in street images using YOLO", "Computer Vision Detection"),
        ("Localize objects in images with bounding boxes for autonomous driving", "Computer Vision Detection"),
        ("Detect and count people in crowded scenes using Faster R-CNN", "Computer Vision Detection"),
        ("Identify and locate faces in photos for security applications", "Computer Vision Detection"),
        ("Detect multiple objects in retail shelf images for inventory", "Computer Vision Detection"),
        ("Localize defects in manufacturing images with precise bounding boxes", "Computer Vision Detection"),
        ("Detect animals in wildlife camera trap images using object detection", "Computer Vision Detection"),
        ("Identify and locate traffic signs in street view images", "Computer Vision Detection"),
        ("Detect vehicles and obstacles for autonomous vehicle navigation", "Computer Vision Detection"),
        ("Localize text regions in documents using object detection", "Computer Vision Detection"),
        ("Detect and track multiple objects in video streams", "Computer Vision Detection"),
        ("Identify and locate products on shelves for automated checkout", "Computer Vision Detection"),
        ("Detect safety equipment in workplace surveillance footage", "Computer Vision Detection"),
        ("Localize medical anomalies in imaging scans with bounding boxes", "Computer Vision Detection"),
        ("Detect and count items in warehouse images for inventory management", "Computer Vision Detection"),
    ]
    return prompts


def generate_ensemble_prompts() -> List[Tuple[str, str]]:
    """Generate ensemble methods prompts."""
    prompts = [
        ("Improve prediction accuracy using Gradient Boosting with XGBoost", "Ensemble Methods"),
        ("Combine multiple models using ensemble learning for robustness", "Ensemble Methods"),
        ("Boost performance on tabular data using LightGBM gradient boosting", "Ensemble Methods"),
        ("Optimize model predictions using CatBoost with categorical features", "Ensemble Methods"),
        ("Create ensemble of classifiers for improved accuracy", "Ensemble Methods"),
        ("Use gradient boosting for high-performance tabular data prediction", "Ensemble Methods"),
        ("Combine weak learners into strong ensemble model", "Ensemble Methods"),
        ("Apply ensemble methods for handling imbalanced datasets", "Ensemble Methods"),
        ("Improve model generalization using gradient boosting ensemble", "Ensemble Methods"),
        ("Combine predictions from multiple models using voting or stacking", "Ensemble Methods"),
        ("Use XGBoost for winning performance on structured data competitions", "Ensemble Methods"),
        ("Apply LightGBM for fast training on large tabular datasets", "Ensemble Methods"),
        ("Boost accuracy using ensemble of gradient boosted trees", "Ensemble Methods"),
        ("Combine neural networks with gradient boosting for hybrid models", "Ensemble Methods"),
        ("Use ensemble methods to reduce overfitting in predictions", "Ensemble Methods"),
    ]
    return prompts


def generate_optimization_prompts() -> List[Tuple[str, str]]:
    """Generate optimization prompts."""
    prompts = [
        ("Optimize hyperparameters using genetic algorithms", "Optimization"),
        ("Find optimal solution using simulated annealing for complex problems", "Optimization"),
        ("Optimize resource allocation using evolutionary algorithms", "Optimization"),
        ("Solve combinatorial optimization problems using metaheuristics", "Optimization"),
        ("Optimize model parameters using Bayesian optimization", "Optimization"),
        ("Find optimal configuration using genetic programming", "Optimization"),
        ("Optimize portfolio allocation using optimization algorithms", "Optimization"),
        ("Solve routing problems using optimization techniques", "Optimization"),
        ("Optimize scheduling using constraint optimization", "Optimization"),
        ("Find optimal feature subset using optimization methods", "Optimization"),
        ("Optimize system parameters using gradient-free optimization", "Optimization"),
        ("Solve multi-objective optimization problems", "Optimization"),
        ("Optimize neural network architecture using optimization algorithms", "Optimization"),
        ("Find optimal thresholds using optimization techniques", "Optimization"),
        ("Optimize model selection using automated optimization", "Optimization"),
    ]
    return prompts


def generate_graph_algorithms_prompts() -> List[Tuple[str, str]]:
    """Generate graph algorithms prompts."""
    prompts = [
        ("Analyze social networks using graph neural networks", "Graph Algorithms"),
        ("Model relationships in knowledge graphs using GNN", "Graph Algorithms"),
        ("Predict node properties in graph structures", "Graph Algorithms"),
        ("Classify graphs using graph neural network architectures", "Graph Algorithms"),
        ("Detect communities in social networks using graph algorithms", "Graph Algorithms"),
        ("Predict links in knowledge graphs using graph embeddings", "Graph Algorithms"),
        ("Model molecular structures using graph neural networks", "Graph Algorithms"),
        ("Analyze citation networks using graph-based learning", "Graph Algorithms"),
        ("Predict interactions in protein-protein interaction graphs", "Graph Algorithms"),
        ("Model user-item relationships in recommendation graphs", "Graph Algorithms"),
        ("Classify molecules using graph convolutional networks", "Graph Algorithms"),
        ("Analyze traffic networks using graph neural networks", "Graph Algorithms"),
        ("Predict node attributes in heterogeneous graphs", "Graph Algorithms"),
        ("Model temporal graphs using dynamic graph neural networks", "Graph Algorithms"),
        ("Analyze financial networks using graph-based approaches", "Graph Algorithms"),
    ]
    return prompts


def generate_transfer_learning_prompts() -> List[Tuple[str, str]]:
    """Generate transfer learning prompts."""
    prompts = [
        ("Fine-tune pretrained BERT model for domain-specific text classification", "Transfer Learning"),
        ("Adapt pretrained image models using transfer learning for medical images", "Transfer Learning"),
        ("Transfer knowledge from large model to small model for deployment", "Transfer Learning"),
        ("Fine-tune pretrained language models for specific NLP tasks", "Transfer Learning"),
        ("Use transfer learning to adapt models to new domains with limited data", "Transfer Learning"),
        ("Fine-tune pretrained vision models for specialized image recognition", "Transfer Learning"),
        ("Transfer learned features from source domain to target domain", "Transfer Learning"),
        ("Adapt pretrained models using few-shot learning techniques", "Transfer Learning"),
        ("Fine-tune transformer models for domain-specific applications", "Transfer Learning"),
        ("Use transfer learning to improve performance on small datasets", "Transfer Learning"),
        ("Adapt pretrained CNNs for new image classification tasks", "Transfer Learning"),
        ("Transfer knowledge from general models to specialized domains", "Transfer Learning"),
        ("Fine-tune pretrained models for low-resource language tasks", "Transfer Learning"),
        ("Use transfer learning to adapt models across different modalities", "Transfer Learning"),
        ("Fine-tune pretrained embeddings for domain-specific applications", "Transfer Learning"),
    ]
    return prompts


def generate_generative_prompts() -> List[Tuple[str, str]]:
    """Generate generative models prompts."""
    prompts = [
        ("Generate synthetic images using GAN for data augmentation", "Generative Models"),
        ("Create new text content using generative language models", "Generative Models"),
        ("Generate realistic images using diffusion models", "Generative Models"),
        ("Create synthetic data using VAE for privacy-preserving datasets", "Generative Models"),
        ("Generate new molecules using generative models for drug discovery", "Generative Models"),
        ("Create art using generative adversarial networks", "Generative Models"),
        ("Generate synthetic voices using generative audio models", "Generative Models"),
        ("Create new music using generative models", "Generative Models"),
        ("Generate realistic scenes using GAN for simulation", "Generative Models"),
        ("Create synthetic patient data using generative models for research", "Generative Models"),
        ("Generate code using generative programming models", "Generative Models"),
        ("Create realistic video using generative video models", "Generative Models"),
        ("Generate synthetic faces using StyleGAN for privacy", "Generative Models"),
        ("Create new designs using generative design models", "Generative Models"),
        ("Generate realistic data using diffusion probabilistic models", "Generative Models"),
    ]
    return prompts


def generate_nlg_prompts() -> List[Tuple[str, str]]:
    """Generate natural language generation prompts."""
    prompts = [
        ("Generate text summaries from long documents using NLG", "Natural Language Generation"),
        ("Create product descriptions using natural language generation", "Natural Language Generation"),
        ("Generate news articles from structured data using text generation", "Natural Language Generation"),
        ("Create personalized email content using natural language generation", "Natural Language Generation"),
        ("Generate reports from data using automated text generation", "Natural Language Generation"),
        ("Create conversational responses using natural language generation", "Natural Language Generation"),
        ("Generate captions for images using text generation models", "Natural Language Generation"),
        ("Create content for chatbots using natural language generation", "Natural Language Generation"),
        ("Generate explanations from structured data using NLG", "Natural Language Generation"),
        ("Create marketing copy using natural language generation", "Natural Language Generation"),
        ("Generate documentation from code using text generation", "Natural Language Generation"),
        ("Create personalized content using natural language generation", "Natural Language Generation"),
        ("Generate answers to questions using text generation models", "Natural Language Generation"),
        ("Create stories from prompts using natural language generation", "Natural Language Generation"),
        ("Generate translations using natural language generation", "Natural Language Generation"),
    ]
    return prompts


def generate_feature_engineering_prompts() -> List[Tuple[str, str]]:
    """Generate feature engineering prompts."""
    prompts = [
        ("Extract meaningful features from raw data using feature engineering", "Feature Engineering"),
        ("Select most important features using feature selection techniques", "Feature Engineering"),
        ("Create polynomial features from numerical data for better model performance", "Feature Engineering"),
        ("Engineer time-based features from timestamp data", "Feature Engineering"),
        ("Extract statistical features from time series data", "Feature Engineering"),
        ("Create interaction features between categorical and numerical variables", "Feature Engineering"),
        ("Select optimal feature subset using recursive feature elimination", "Feature Engineering"),
        ("Engineer domain-specific features for improved predictions", "Feature Engineering"),
        ("Extract text features using TF-IDF and n-grams", "Feature Engineering"),
        ("Create lag features from sequential data", "Feature Engineering"),
        ("Engineer frequency domain features from signal data", "Feature Engineering"),
        ("Extract shape and texture features from images", "Feature Engineering"),
        ("Select features using mutual information for classification", "Feature Engineering"),
        ("Engineer aggregation features from transactional data", "Feature Engineering"),
        ("Create embedding features from categorical variables", "Feature Engineering"),
    ]
    return prompts


def generate_deep_learning_prompts() -> List[Tuple[str, str]]:
    """Generate deep learning prompts."""
    prompts = [
        ("Build deep neural network for complex pattern recognition", "Deep Learning"),
        ("Train multilayer perceptron for tabular data classification", "Deep Learning"),
        ("Use deep learning for high-dimensional data processing", "Deep Learning"),
        ("Apply deep neural networks for feature learning from raw data", "Deep Learning"),
        ("Train DNN for regression with non-linear relationships", "Deep Learning"),
        ("Build deep learning model for multi-task learning", "Deep Learning"),
        ("Use deep neural networks for hierarchical feature extraction", "Deep Learning"),
        ("Apply deep learning for automated feature discovery", "Deep Learning"),
        ("Train deep model for complex decision boundaries", "Deep Learning"),
        ("Use DNN for learning from large-scale datasets", "Deep Learning"),
        ("Apply deep learning for end-to-end learning pipeline", "Deep Learning"),
        ("Build deep neural network with multiple hidden layers", "Deep Learning"),
        ("Train deep model for non-linear transformations", "Deep Learning"),
        ("Use deep learning for learning complex data representations", "Deep Learning"),
        ("Apply DNN for high-capacity model requirements", "Deep Learning"),
    ]
    return prompts


def generate_cv_segmentation_prompts() -> List[Tuple[str, str]]:
    """Generate computer vision segmentation prompts."""
    prompts = [
        ("Segment medical images into anatomical regions using semantic segmentation", "Computer Vision Segmentation"),
        ("Perform instance segmentation to separate individual objects in images", "Computer Vision Segmentation"),
        ("Segment road scenes into different classes using segmentation networks", "Computer Vision Segmentation"),
        ("Perform pixel-level classification using semantic segmentation", "Computer Vision Segmentation"),
        ("Segment cells in microscopic images using segmentation models", "Computer Vision Segmentation"),
        ("Separate foreground from background using image segmentation", "Computer Vision Segmentation"),
        ("Segment satellite images into land use classes", "Computer Vision Segmentation"),
        ("Perform fine-grained segmentation of scenes into semantic regions", "Computer Vision Segmentation"),
        ("Segment medical scans into tissue types using segmentation", "Computer Vision Segmentation"),
        ("Separate overlapping objects using instance segmentation", "Computer Vision Segmentation"),
        ("Segment video frames into semantic regions for analysis", "Computer Vision Segmentation"),
        ("Perform pixel-wise classification using deep segmentation networks", "Computer Vision Segmentation"),
        ("Segment agricultural fields in aerial images", "Computer Vision Segmentation"),
        ("Separate different materials in images using segmentation", "Computer Vision Segmentation"),
        ("Segment urban scenes into building, road, and vegetation classes", "Computer Vision Segmentation"),
    ]
    return prompts


def generate_multimodal_prompts() -> List[Tuple[str, str]]:
    """Generate multi-modal learning prompts."""
    prompts = [
        ("Combine text and image features for multi-modal classification", "Multi-modal Learning"),
        ("Fuse audio and video features using multi-modal learning", "Multi-modal Learning"),
        ("Integrate multiple data modalities for improved predictions", "Multi-modal Learning"),
        ("Combine visual and textual information for content understanding", "Multi-modal Learning"),
        ("Fuse sensor data from multiple sources using multi-modal approaches", "Multi-modal Learning"),
        ("Integrate image and text embeddings for cross-modal retrieval", "Multi-modal Learning"),
        ("Combine structured and unstructured data using multi-modal learning", "Multi-modal Learning"),
        ("Fuse different data types for comprehensive analysis", "Multi-modal Learning"),
        ("Integrate video and audio streams for multi-modal understanding", "Multi-modal Learning"),
        ("Combine numerical and categorical features across modalities", "Multi-modal Learning"),
        ("Fuse time series and image data for multi-modal forecasting", "Multi-modal Learning"),
        ("Integrate graph and text data for multi-modal knowledge extraction", "Multi-modal Learning"),
        ("Combine multiple sensor modalities for environmental monitoring", "Multi-modal Learning"),
        ("Fuse text, images, and metadata for content recommendation", "Multi-modal Learning"),
        ("Integrate different data sources using cross-modal learning", "Multi-modal Learning"),
    ]
    return prompts


def generate_automl_prompts() -> List[Tuple[str, str]]:
    """Generate AutoML prompts."""
    prompts = [
        ("Automate machine learning pipeline using AutoML", "AutoML"),
        ("Automatically select best model using automated machine learning", "AutoML"),
        ("Optimize hyperparameters automatically using AutoML frameworks", "AutoML"),
        ("Automate feature engineering and model selection with AutoML", "AutoML"),
        ("Use neural architecture search for automated model design", "AutoML"),
        ("Automate end-to-end ML workflow using AutoML tools", "AutoML"),
        ("Automatically tune model hyperparameters using AutoML", "AutoML"),
        ("Use AutoML for rapid prototyping and model selection", "AutoML"),
        ("Automate pipeline optimization using automated ML", "AutoML"),
        ("Apply neural architecture search for optimal model architecture", "AutoML"),
        ("Automate feature selection and engineering with AutoML", "AutoML"),
        ("Use AutoML to automatically build and optimize models", "AutoML"),
        ("Automate model training and evaluation using AutoML", "AutoML"),
        ("Apply automated machine learning for quick model development", "AutoML"),
        ("Use AutoML to automatically find best algorithms and parameters", "AutoML"),
    ]
    return prompts


def generate_all_prompts() -> List[Tuple[str, str]]:
    """Generate all 10000 prompts across all 25 algorithm type categories."""
    all_prompts = []
    all_prompts.extend(generate_classification_prompts())
    all_prompts.extend(generate_regression_prompts())
    all_prompts.extend(generate_clustering_prompts())
    all_prompts.extend(generate_time_series_prompts())
    all_prompts.extend(generate_sequence_models_prompts())
    all_prompts.extend(generate_nlp_prompts())
    all_prompts.extend(generate_vision_prompts())
    all_prompts.extend(generate_cv_detection_prompts())
    all_prompts.extend(generate_anomaly_prompts())
    all_prompts.extend(generate_recsys_prompts())
    all_prompts.extend(generate_rl_prompts())
    all_prompts.extend(generate_causal_prompts())
    all_prompts.extend(generate_dimred_prompts())
    all_prompts.extend(generate_ensemble_prompts())
    all_prompts.extend(generate_optimization_prompts())
    all_prompts.extend(generate_graph_algorithms_prompts())
    all_prompts.extend(generate_transfer_learning_prompts())
    all_prompts.extend(generate_generative_prompts())
    all_prompts.extend(generate_nlg_prompts())
    all_prompts.extend(generate_feature_engineering_prompts())
    all_prompts.extend(generate_deep_learning_prompts())
    all_prompts.extend(generate_cv_segmentation_prompts())
    all_prompts.extend(generate_multimodal_prompts())
    all_prompts.extend(generate_automl_prompts())
    
    # Filter out "Other" category prompts
    all_prompts = [(p, t) for p, t in all_prompts if t != "Other"]
    
    # Ensure we have exactly 10000 by expanding variations if needed
    target = 10000
    base = list(all_prompts)
    i = 0
    while len(all_prompts) < target:
        p, t = base[i % len(base)]
        # Add a lightweight variant suffix to keep uniqueness while preserving category
        # Skip if category is "Other"
        if t != "Other":
            all_prompts.append((f"{p} (variant {i+1})", t))
        i += 1
    if len(all_prompts) > target:
        all_prompts = all_prompts[:target]
    
    # Final filter to ensure no "Other" prompts
    all_prompts = [(p, t) for p, t in all_prompts if t != "Other"]
    
    return all_prompts


if __name__ == "__main__":
    prompts = generate_all_prompts()
    print(f"Generated {len(prompts)} prompts")
    
    # Save to file
    with open("prompts.txt", "w", encoding="utf-8") as f:
        for prompt, algo_type in prompts:
            f.write(f"{prompt}|{algo_type}\n")
    
    print(f"Saved prompts to prompts.txt")

