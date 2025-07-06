#!/usr/bin/env python3
"""
Model Persistence and Hyperparameter Optimization
===============================================

Utilities for saving and loading trained models, and performing
hyperparameter optimization for real estate pricing models.

Author: Lucas P
Date: July 6, 2025
"""

import os
import json
import joblib
import pickle
import logging
from typing import Dict, Any, List, Tuple, Union, Optional
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, make_scorer

# Setup logging
logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Registry for managing trained models with version control and metadata.
    
    This class provides functionality to save, load, and manage trained models,
    including their associated metadata, performance metrics, and feature importance.
    """
    
    def __init__(self, registry_path: Union[str, Path] = "models"):
        """
        Initialize the model registry.
        
        Args:
            registry_path: Path to the directory where models will be stored
        """
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.models_index_path = self.registry_path / "models_index.json"
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing model index or create a new one."""
        if self.models_index_path.exists():
            try:
                with open(self.models_index_path, "r") as f:
                    self.index = json.load(f)
                logger.info(f"Loaded model index with {len(self.index)} entries")
            except Exception as e:
                logger.warning(f"Error loading model index: {e}. Creating new index.")
                self.index = {}
        else:
            self.index = {}
    
    def _save_index(self):
        """Save the model index to disk."""
        with open(self.models_index_path, "w") as f:
            json.dump(self.index, f, indent=2)
        logger.info(f"Saved model index with {len(self.index)} entries")
    
    def save_model(
        self, 
        model: BaseEstimator,
        model_name: str,
        feature_names: List[str],
        metrics: Dict[str, float],
        metadata: Dict[str, Any] = None,
        model_version: Optional[str] = None,
        feature_importance: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Save a trained model to the registry.
        
        Args:
            model: The trained model to save
            model_name: Name of the model (e.g., 'price_prediction')
            feature_names: List of feature names used in training
            metrics: Dictionary of performance metrics
            metadata: Additional metadata about the model
            model_version: Version string (if None, timestamp will be used)
            feature_importance: Dictionary mapping feature names to importance scores
            
        Returns:
            The model ID in the registry
        """
        # Create a timestamp-based version if not provided
        if model_version is None:
            model_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create model ID
        model_id = f"{model_name}_{model_version}"
        
        # Create metadata
        model_metadata = metadata or {}
        model_metadata.update({
            "model_name": model_name,
            "model_version": model_version,
            "model_id": model_id,
            "created_at": datetime.now().isoformat(),
            "feature_names": feature_names,
            "metrics": metrics,
            "feature_importance": feature_importance
        })
        
        # Create model directory
        model_dir = self.registry_path / model_id
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model using joblib
        model_path = model_dir / "model.joblib"
        joblib.dump(model, model_path)
        logger.info(f"Saved model to {model_path}")
        
        # Save metadata
        metadata_path = model_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(model_metadata, f, indent=2)
        logger.info(f"Saved model metadata to {metadata_path}")
        
        # Update index
        self.index[model_id] = {
            "model_name": model_name,
            "model_version": model_version,
            "path": str(model_dir),
            "created_at": model_metadata["created_at"],
            "metrics": metrics
        }
        self._save_index()
        
        return model_id
    
    def load_model(self, model_id: str) -> Tuple[BaseEstimator, Dict[str, Any]]:
        """
        Load a model from the registry.
        
        Args:
            model_id: ID of the model to load
            
        Returns:
            Tuple of (model, metadata)
        """
        if model_id not in self.index:
            raise ValueError(f"Model {model_id} not found in registry")
        
        model_dir = Path(self.index[model_id]["path"])
        
        # Load model
        model_path = model_dir / "model.joblib"
        model = joblib.load(model_path)
        logger.info(f"Loaded model from {model_path}")
        
        # Load metadata
        metadata_path = model_dir / "metadata.json"
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        logger.info(f"Loaded model metadata from {metadata_path}")
        
        return model, metadata
    
    def get_best_model(self, model_name: str, metric: str = "r2_score", higher_is_better: bool = True) -> str:
        """
        Get the best model for a given model name based on a metric.
        
        Args:
            model_name: Name of the model
            metric: Metric to use for comparison
            higher_is_better: Whether higher values of the metric are better
            
        Returns:
            ID of the best model
        """
        # Filter models by name
        matching_models = {
            model_id: info for model_id, info in self.index.items()
            if info["model_name"] == model_name and metric in info["metrics"]
        }
        
        if not matching_models:
            raise ValueError(f"No models found with name {model_name} and metric {metric}")
        
        # Find the best model
        if higher_is_better:
            best_model_id = max(matching_models, key=lambda m: matching_models[m]["metrics"][metric])
        else:
            best_model_id = min(matching_models, key=lambda m: matching_models[m]["metrics"][metric])
        
        return best_model_id
    
    def delete_model(self, model_id: str) -> bool:
        """
        Delete a model from the registry.
        
        Args:
            model_id: ID of the model to delete
            
        Returns:
            True if successful, False otherwise
        """
        if model_id not in self.index:
            logger.warning(f"Model {model_id} not found in registry")
            return False
        
        # Get model directory
        model_dir = Path(self.index[model_id]["path"])
        
        try:
            # Remove model files
            for file_path in model_dir.glob("*"):
                file_path.unlink()
            
            # Remove directory
            model_dir.rmdir()
            
            # Remove from index
            del self.index[model_id]
            self._save_index()
            
            logger.info(f"Deleted model {model_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting model {model_id}: {e}")
            return False
    
    def list_models(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all models in the registry.
        
        Args:
            model_name: Filter by model name (optional)
            
        Returns:
            List of model information dictionaries
        """
        if model_name:
            # Filter by model name
            return [
                {**info, "model_id": model_id} 
                for model_id, info in self.index.items()
                if info["model_name"] == model_name
            ]
        else:
            # Return all models
            return [
                {**info, "model_id": model_id} 
                for model_id, info in self.index.items()
            ]


class HyperparameterOptimizer:
    """
    Optimize hyperparameters for machine learning models.
    
    This class provides utilities for hyperparameter optimization using
    both grid search and randomized search approaches.
    """
    
    def __init__(
        self, 
        pipeline: Pipeline,
        param_grid: Dict[str, Any],
        cv: int = 5,
        scoring: str = 'neg_mean_squared_error',
        n_jobs: int = -1
    ):
        """
        Initialize the hyperparameter optimizer.
        
        Args:
            pipeline: The scikit-learn pipeline to optimize
            param_grid: Parameter grid for hyperparameter search
            cv: Number of cross-validation folds
            scoring: Scoring metric to use
            n_jobs: Number of parallel jobs (-1 for all processors)
        """
        self.pipeline = pipeline
        self.param_grid = param_grid
        self.cv = cv
        self.scoring = scoring
        self.n_jobs = n_jobs
        self.best_estimator_ = None
        self.best_params_ = None
        self.results_ = None
    
    def grid_search(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Perform grid search for hyperparameter optimization.
        
        Args:
            X: Feature matrix
            y: Target vector
            
        Returns:
            Dictionary with optimization results
        """
        logger.info("Starting grid search for hyperparameter optimization")
        
        # Create the grid search estimator
        grid_search = GridSearchCV(
            estimator=self.pipeline,
            param_grid=self.param_grid,
            cv=self.cv,
            scoring=self.scoring,
            n_jobs=self.n_jobs,
            verbose=1,
            return_train_score=True
        )
        
        # Fit the grid search
        grid_search.fit(X, y)
        
        # Store results
        self.best_estimator_ = grid_search.best_estimator_
        self.best_params_ = grid_search.best_params_
        self.results_ = {
            "best_score": grid_search.best_score_,
            "best_params": grid_search.best_params_,
            "cv_results": {
                k: v.tolist() if isinstance(v, np.ndarray) else v
                for k, v in grid_search.cv_results_.items()
            }
        }
        
        logger.info(f"Grid search complete. Best score: {grid_search.best_score_}")
        logger.info(f"Best parameters: {grid_search.best_params_}")
        
        return self.results_
    
    def randomized_search(
        self, 
        X: pd.DataFrame, 
        y: pd.Series,
        n_iter: int = 100,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Perform randomized search for hyperparameter optimization.
        
        Args:
            X: Feature matrix
            y: Target vector
            n_iter: Number of parameter settings to sample
            random_state: Random state for reproducibility
            
        Returns:
            Dictionary with optimization results
        """
        logger.info(f"Starting randomized search with {n_iter} iterations")
        
        # Create the randomized search estimator
        random_search = RandomizedSearchCV(
            estimator=self.pipeline,
            param_distributions=self.param_grid,
            n_iter=n_iter,
            cv=self.cv,
            scoring=self.scoring,
            n_jobs=self.n_jobs,
            verbose=1,
            random_state=random_state,
            return_train_score=True
        )
        
        # Fit the randomized search
        random_search.fit(X, y)
        
        # Store results
        self.best_estimator_ = random_search.best_estimator_
        self.best_params_ = random_search.best_params_
        self.results_ = {
            "best_score": random_search.best_score_,
            "best_params": random_search.best_params_,
            "cv_results": {
                k: v.tolist() if isinstance(v, np.ndarray) else v
                for k, v in random_search.cv_results_.items()
            }
        }
        
        logger.info(f"Randomized search complete. Best score: {random_search.best_score_}")
        logger.info(f"Best parameters: {random_search.best_params_}")
        
        return self.results_
    
    def save_results(self, output_path: Union[str, Path]) -> str:
        """
        Save optimization results to a file.
        
        Args:
            output_path: Path where results will be saved
            
        Returns:
            Path to the saved results file
        """
        if self.results_ is None:
            raise ValueError("No optimization results available")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(self.results_, f, indent=2)
        
        logger.info(f"Saved optimization results to {output_path}")
        return str(output_path)


# Default parameter grids for common models
DEFAULT_PARAM_GRIDS = {
    "linear_regression": {
        "model__fit_intercept": [True, False]
    },
    "ridge": {
        "model__alpha": [0.01, 0.1, 1.0, 10.0, 100.0],
        "model__fit_intercept": [True, False]
    },
    "lasso": {
        "model__alpha": [0.01, 0.1, 1.0, 10.0, 100.0],
        "model__fit_intercept": [True, False]
    },
    "random_forest": {
        "model__n_estimators": [50, 100, 200],
        "model__max_depth": [None, 10, 20, 30],
        "model__min_samples_split": [2, 5, 10],
        "model__min_samples_leaf": [1, 2, 4]
    },
    "gradient_boosting": {
        "model__n_estimators": [50, 100, 200],
        "model__learning_rate": [0.01, 0.1, 0.2],
        "model__max_depth": [3, 4, 5],
        "model__subsample": [0.8, 0.9, 1.0]
    }
}


def get_default_param_grid(model_type: str) -> Dict[str, Any]:
    """
    Get default parameter grid for a model type.
    
    Args:
        model_type: Type of model
        
    Returns:
        Parameter grid dictionary
    """
    if model_type not in DEFAULT_PARAM_GRIDS:
        raise ValueError(f"No default parameter grid for model type: {model_type}")
    
    return DEFAULT_PARAM_GRIDS[model_type].copy()


def evaluate_model(
    model: BaseEstimator,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    feature_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Evaluate a trained model on test data.
    
    Args:
        model: Trained model to evaluate
        X_test: Test feature matrix
        y_test: Test target vector
        feature_names: List of feature names (optional)
        
    Returns:
        Dictionary with evaluation metrics and feature importance
    """
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    metrics = {
        "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
        "mae": mean_absolute_error(y_test, y_pred),
        "r2_score": r2_score(y_test, y_pred)
    }
    
    # Calculate residuals
    residuals = y_test - y_pred
    metrics["mean_residual"] = np.mean(residuals)
    metrics["std_residual"] = np.std(residuals)
    
    # Extract feature importance if available
    feature_importance = None
    if hasattr(model, 'feature_importances_') and feature_names is not None:
        feature_importance = {
            name: float(importance)
            for name, importance in zip(feature_names, model.feature_importances_)
        }
    elif hasattr(model, 'coef_') and feature_names is not None:
        feature_importance = {
            name: float(coef)
            for name, coef in zip(feature_names, model.coef_)
        }
    
    # Compile results
    results = {
        "metrics": metrics,
        "feature_importance": feature_importance
    }
    
    return results
