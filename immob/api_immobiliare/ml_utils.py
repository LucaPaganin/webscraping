#!/usr/bin/env python3
"""
Real Estate Machine Learning Utilities
=====================================

Functions and utilities for machine learning on real estate data.

Author: Lucas P
Date: July 6, 2025
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor


def evaluate_model(model, X_train, X_test, y_train, y_test):
    """
    Evaluate a model's performance with detailed metrics.
    
    Args:
        model: Trained model instance
        X_train: Training features
        X_test: Testing features
        y_train: Training target values
        y_test: Testing target values
        
    Returns:
        Dictionary of evaluation metrics
    """
    # Make predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Calculate metrics
    metrics = {
        'train_rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
        'test_rmse': np.sqrt(mean_squared_error(y_test, y_test_pred)),
        'train_mae': mean_absolute_error(y_train, y_train_pred),
        'test_mae': mean_absolute_error(y_test, y_test_pred),
        'train_r2': r2_score(y_train, y_train_pred),
        'test_r2': r2_score(y_test, y_test_pred),
        'test_mape': np.mean(np.abs((y_test - y_test_pred) / y_test)) * 100
    }
    
    return metrics


def build_model_pipeline(model, preprocessor=None, column_info=None):
    """
    Build a complete model pipeline with preprocessing.
    
    Args:
        model: Model instance to use for prediction
        preprocessor: Optional preprocessing pipeline
        column_info: Dictionary of column groupings
        
    Returns:
        Complete pipeline including preprocessing and model
    """
    steps = []
    
    if preprocessor:
        steps.append(('preprocessor', preprocessor))
    
    steps.append(('model', model))
    
    return Pipeline(steps=steps)


def evaluate_model_pipeline(pipeline, X_train, X_test, y_train, y_test, model_name="Model"):
    """
    Evaluate a model pipeline and display results.
    
    Args:
        pipeline: Complete model pipeline
        X_train: Training features
        X_test: Testing features
        y_train: Training target values
        y_test: Testing target values
        model_name: Name of the model for display
        
    Returns:
        Dictionary of evaluation metrics
    """
    # Train model
    pipeline.fit(X_train, y_train)
    
    # Make predictions
    y_train_pred = pipeline.predict(X_train)
    y_test_pred = pipeline.predict(X_test)
    
    # Calculate metrics
    metrics = {
        'train_rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
        'test_rmse': np.sqrt(mean_squared_error(y_test, y_test_pred)),
        'train_mae': mean_absolute_error(y_train, y_train_pred),
        'test_mae': mean_absolute_error(y_test, y_test_pred),
        'train_r2': r2_score(y_train, y_train_pred),
        'test_r2': r2_score(y_test, y_test_pred),
        'test_mape': np.mean(np.abs((y_test - y_test_pred) / y_test)) * 100
    }
    
    # Print results
    print(f"\n{model_name} Evaluation Metrics:")
    print(f"Training RMSE: {metrics['train_rmse']:.2f} €")
    print(f"Testing RMSE: {metrics['test_rmse']:.2f} €")
    print(f"Training MAE: {metrics['train_mae']:.2f} €")
    print(f"Testing MAE: {metrics['test_mae']:.2f} €")
    print(f"Training R²: {metrics['train_r2']:.4f}")
    print(f"Testing R²: {metrics['test_r2']:.4f}")
    print(f"Testing MAPE: {metrics['test_mape']:.2f}%")
    
    # Create scatter plot of predicted vs actual values
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_test_pred, alpha=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--')
    plt.xlabel('Actual Price (€)')
    plt.ylabel('Predicted Price (€)')
    plt.title(f'{model_name}: Actual vs Predicted Prices')
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    return metrics


def train_multiple_models(X_train, X_test, y_train, y_test, preprocessor=None):
    """
    Train and evaluate multiple regression models.
    
    Args:
        X_train: Training features
        X_test: Testing features
        y_train: Training target values
        y_test: Testing target values
        preprocessor: Optional preprocessing pipeline
        
    Returns:
        Dictionary of model names and their evaluation metrics
    """
    models = {
        'Linear Regression': LinearRegression(),
        'Ridge Regression': Ridge(alpha=1.0),
        'Lasso Regression': Lasso(alpha=0.1),
        'ElasticNet': ElasticNet(alpha=0.1, l1_ratio=0.5),
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
        'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
        'SVR': SVR(kernel='rbf'),
        'KNN': KNeighborsRegressor(n_neighbors=5)
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"\n{'-'*40}\nTraining {name}...\n{'-'*40}")
        
        # Create pipeline
        pipeline = build_model_pipeline(model, preprocessor)
        
        # Train and evaluate
        metrics = evaluate_model_pipeline(pipeline, X_train, X_test, y_train, y_test, name)
        results[name] = metrics
    
    # Create comparison table
    compare_df = pd.DataFrame({
        model_name: {
            'Test RMSE': metrics['test_rmse'],
            'Test MAE': metrics['test_mae'],
            'Test R²': metrics['test_r2'],
            'Test MAPE': metrics['test_mape']
        }
        for model_name, metrics in results.items()
    }).T
    
    # Sort by R²
    compare_df = compare_df.sort_values('Test R²', ascending=False)
    
    print("\nModel Comparison:")
    print(compare_df)
    
    return results


def select_features(X_train, y_train, X_test, n_features=20, method='f_regression'):
    """
    Select top features based on statistical tests.
    
    Args:
        X_train: Training features
        y_train: Training target values
        X_test: Testing features
        n_features: Number of features to select
        method: Method for feature selection ('f_regression' or 'mutual_info')
        
    Returns:
        Tuple of (X_train_selected, X_test_selected, selected_features_mask, selector)
    """
    if method == 'f_regression':
        selector = SelectKBest(f_regression, k=n_features)
    else:
        selector = SelectKBest(mutual_info_regression, k=n_features)
    
    # Fit and transform
    X_train_selected = selector.fit_transform(X_train, y_train)
    X_test_selected = selector.transform(X_test)
    
    # Get selected features mask
    selected_features_mask = selector.get_support()
    
    return X_train_selected, X_test_selected, selected_features_mask, selector


def tune_model_hyperparameters(model, param_grid, X_train, y_train, cv=5):
    """
    Tune model hyperparameters using grid search.
    
    Args:
        model: Model instance
        param_grid: Parameter grid for search
        X_train: Training features
        y_train: Training target values
        cv: Number of cross-validation folds
        
    Returns:
        Best model instance with optimized hyperparameters
    """
    grid_search = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        cv=cv,
        scoring='neg_mean_squared_error',
        verbose=1,
        n_jobs=-1
    )
    
    grid_search.fit(X_train, y_train)
    
    print(f"Best parameters: {grid_search.best_params_}")
    print(f"Best score: {np.sqrt(-grid_search.best_score_)}")
    
    return grid_search.best_estimator_


def plot_feature_importance(model, feature_names):
    """
    Plot feature importance for tree-based models.
    
    Args:
        model: Trained tree-based model with feature_importances_ attribute
        feature_names: List of feature names
    """
    if not hasattr(model, 'feature_importances_'):
        print("Model doesn't have feature_importances_ attribute")
        return
    
    # Get feature importances
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    # Plot feature importances
    plt.figure(figsize=(12, 8))
    plt.title('Feature Importances')
    plt.bar(range(len(indices)), importances[indices], align='center')
    plt.xticks(range(len(indices)), [feature_names[i] for i in indices], rotation=90)
    plt.tight_layout()
    plt.show()
    
    # Print top features
    print("\nTop 20 features:")
    for i, idx in enumerate(indices[:20]):
        print(f"{i+1}. {feature_names[idx]}: {importances[idx]:.4f}")


def plot_prediction_residuals(y_true, y_pred):
    """
    Plot prediction residuals.
    
    Args:
        y_true: Actual target values
        y_pred: Predicted target values
    """
    residuals = y_true - y_pred
    
    plt.figure(figsize=(12, 5))
    
    # Residuals vs predicted plot
    plt.subplot(1, 2, 1)
    plt.scatter(y_pred, residuals, alpha=0.5)
    plt.axhline(y=0, color='r', linestyle='-')
    plt.xlabel('Predicted Values')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Predicted Values')
    plt.grid(True)
    
    # Residuals distribution
    plt.subplot(1, 2, 2)
    sns.histplot(residuals, kde=True)
    plt.xlabel('Residuals')
    plt.title('Residuals Distribution')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # Calculate residual statistics
    print("\nResiduals Statistics:")
    print(f"Mean: {residuals.mean():.2f}")
    print(f"Median: {np.median(residuals):.2f}")
    print(f"Standard Deviation: {residuals.std():.2f}")
    print(f"Min: {residuals.min():.2f}")
    print(f"Max: {residuals.max():.2f}")
    
    # Calculate quartiles
    q1, q3 = np.percentile(residuals, [25, 75])
    iqr = q3 - q1
    print(f"IQR: {iqr:.2f}")
    print(f"Q1 (25%): {q1:.2f}")
    print(f"Q3 (75%): {q3:.2f}")
    
    # Check for outliers in residuals
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = ((residuals < lower_bound) | (residuals > upper_bound)).sum()
    print(f"Number of outlier residuals: {outliers} ({outliers/len(residuals)*100:.2f}%)")


def train_model_with_selected_features(X, y, model_type='random_forest', n_features=20, 
                                      selection_method='f_regression', test_size=0.2, 
                                      random_state=42):
    """
    Train a model using feature selection.
    
    Args:
        X: Feature matrix
        y: Target values
        model_type: Type of model to train ('random_forest', 'linear', etc.)
        n_features: Number of features to select
        selection_method: Method for feature selection
        test_size: Test set proportion
        random_state: Random seed
        
    Returns:
        Dictionary with model, performance metrics, and feature information
    """
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    # Select features
    X_train_selected, X_test_selected, selected_mask, selector = select_features(
        X_train, y_train, X_test, n_features=n_features, method=selection_method
    )
    
    # Get selected feature names
    feature_names = X.columns
    selected_features = feature_names[selected_mask]
    
    # Print selected features
    print(f"Selected {len(selected_features)} features using {selection_method}:")
    for i, feature in enumerate(selected_features):
        if hasattr(selector, 'scores_'):
            score = selector.scores_[selected_mask][i]
            print(f"{i+1}. {feature} (Score: {score:.4f})")
        else:
            print(f"{i+1}. {feature}")
    
    # Create model
    if model_type == 'random_forest':
        model = RandomForestRegressor(n_estimators=100, random_state=random_state)
    elif model_type == 'gradient_boosting':
        model = GradientBoostingRegressor(n_estimators=100, random_state=random_state)
    elif model_type == 'linear':
        model = LinearRegression()
    elif model_type == 'ridge':
        model = Ridge(alpha=1.0)
    elif model_type == 'lasso':
        model = Lasso(alpha=0.1)
    else:
        model = RandomForestRegressor(n_estimators=100, random_state=random_state)
    
    # Train model
    model.fit(X_train_selected, y_train)
    
    # Make predictions
    y_train_pred = model.predict(X_train_selected)
    y_test_pred = model.predict(X_test_selected)
    
    # Evaluate model
    metrics = evaluate_model(model, X_train_selected, X_test_selected, y_train, y_test)
    
    # Print results
    print(f"\n{model_type.replace('_', ' ').title()} with {selection_method} Feature Selection:")
    print(f"Training R²: {metrics['train_r2']:.4f}")
    print(f"Testing R²: {metrics['test_r2']:.4f}")
    print(f"Testing RMSE: {metrics['test_rmse']:.2f}")
    print(f"Testing MAPE: {metrics['test_mape']:.2f}%")
    
    # Plot actual vs predicted values
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_test_pred, alpha=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--')
    plt.xlabel('Actual Price (€)')
    plt.ylabel('Predicted Price (€)')
    plt.title(f'{model_type.replace("_", " ").title()} with {selection_method}: Actual vs Predicted Prices')
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    # Plot residuals if it's a tree-based model
    if model_type in ['random_forest', 'gradient_boosting']:
        plot_feature_importance(model, selected_features)
    
    plot_prediction_residuals(y_test, y_test_pred)
    
    return {
        'model': model,
        'metrics': metrics,
        'selected_features': selected_features,
        'selected_mask': selected_mask,
        'selector': selector,
        'X_train_selected': X_train_selected,
        'X_test_selected': X_test_selected,
        'y_train': y_train,
        'y_test': y_test,
        'y_train_pred': y_train_pred,
        'y_test_pred': y_test_pred
    }
