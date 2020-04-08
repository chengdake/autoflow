from collections import defaultdict
from contextlib import redirect_stderr
from io import StringIO
from time import time

import numpy as np
from ConfigSpace import Configuration

from dsmac.runhistory.utils import get_id_of_config
from hyperflow.constants import MLTask
from hyperflow.manager.resource_manager import ResourceManager
from hyperflow.manager.data_manager import DataManager
from hyperflow.metrics import Scorer, calculate_score
from hyperflow.pipeline.dataframe import GenericDataFrame
from hyperflow.pipeline.pipeline import GenericPipeline
from hyperflow.utils.data import mean_predicts, vote_predicts
from hyperflow.utils.logging_ import get_logger


class TrainEvaluator():
    def __init__(self):
        self.resource_manager = None

    def init_data(
            self,
            data_manager: DataManager,
            metric: Scorer,
            all_scoring_functions: bool,
            splitter,
            should_store_intermediate_result: bool,
    ):
        self.splitter = splitter
        self.data_manager = data_manager
        self.X_train = self.data_manager.X_train
        self.y_train = self.data_manager.y_train
        self.X_test = self.data_manager.X_test
        self.y_test = self.data_manager.y_test
        self.should_store_intermediate_result = should_store_intermediate_result
        self.metric = metric
        self.ml_task: MLTask = self.data_manager.ml_task

        self.all_scoring_functions = all_scoring_functions

        if self.ml_task.mainTask == "regression":
            self.predict_function = self._predict_regression
        else:
            self.predict_function = self._predict_proba

        logger_name = self.__class__.__name__
        self.logger = get_logger(logger_name)

    def loss(self, y_true, y_hat):
        all_scoring_functions = (
            self.all_scoring_functions
            if self.all_scoring_functions is None
            else self.all_scoring_functions
        )

        score = calculate_score(
            y_true, y_hat, self.ml_task, self.metric,
            all_scoring_functions=all_scoring_functions)

        if isinstance(score, dict):
            err = self.metric._optimum - score[self.metric.name]
            all_score = score
        elif isinstance(score, (int, float)):
            err = self.metric._optimum - score
            all_score = None
        else:
            raise TypeError

        return err, all_score

    def set_resource_manager(self, resource_manager: ResourceManager):
        self.resource_manager = resource_manager

    def _predict_proba(self, X, model):
        Y_pred = model.predict_proba(X)
        return Y_pred

    def _predict_regression(self, X, model):
        Y_pred = model.predict(X)
        if len(Y_pred.shape) == 1:
            Y_pred = Y_pred.reshape((-1, 1))
        return Y_pred

    def get_Xy(self):
        return self.X_train, self.y_train, self.X_test, self.y_test

    def evaluate(self, model: GenericPipeline, X, y, X_test, y_test):
        assert self.resource_manager is not None
        warning_info = StringIO()
        with redirect_stderr(warning_info):
            # splitter 必须存在
            losses = []
            models = []
            y_true_indexes = []
            y_preds = []
            y_test_preds = []
            all_scores = []
            for train_index, valid_index in self.splitter.split(X, y):
                X: GenericDataFrame
                X_train, X_valid = X.split([train_index, valid_index])
                y_train, y_valid = y[train_index], y[valid_index]
                if self.should_store_intermediate_result:
                    intermediate_result = []
                else:
                    intermediate_result = None
                procedure_result = model.procedure(self.ml_task, X_train, y_train, X_valid, y_valid, X_test, y_test,
                                                   self.resource_manager, intermediate_result)
                models.append(model)
                y_true_indexes.append(valid_index)
                y_pred = procedure_result["pred_valid"]
                y_test_pred = procedure_result["pred_test"]
                y_preds.append(y_pred)
                y_test_preds.append(y_test_pred)
                loss, all_score = self.loss(y_valid, y_pred)
                losses.append(float(loss))
                all_scores.append(all_score)

            final_loss = float(np.array(losses).mean())
            if len(all_scores) > 0 and all_scores[0]:
                all_score = defaultdict(list)
                for cur_all_score in all_scores:
                    assert isinstance(cur_all_score, dict)
                    for key, value in cur_all_score.items():
                        all_score[key].append(value)
                for key in all_score.keys():
                    all_score[key] = float(np.mean(all_score[key]))
            else:
                all_score = None
                all_scores = None
            info = {
                "loss": final_loss,
                "losses": losses,
                "all_score": all_score,
                "all_scores": all_scores,
                "models": models,
                "y_true_indexes": y_true_indexes,
                "y_preds": y_preds,
                "intermediate_result": intermediate_result
            }
            # todo
            if y_test is not None:
                # 验证集训练模型的组合去预测测试集的数据
                if self.ml_task.mainTask == "classification":
                    y_test_pred = vote_predicts(y_test_preds)
                else:
                    y_test_pred = mean_predicts(y_test_preds)
                test_loss, test_all_score = self.loss(y_test, y_test_pred)
                info.update({
                    "test_loss": test_loss,
                    "test_all_score": test_all_score,
                    "y_test_true": y_test,
                    "y_test_pred": y_test_pred
                })
        info["warning_info"] = warning_info.getvalue()
        return final_loss, info

    def set_shp2model(self, shp2model):
        self.shp2model = shp2model

    def __call__(self, shp: Configuration):
        # 1. 将php变成model
        config_id = get_id_of_config(shp)
        start = time()
        dhp, model = self.shp2model(shp)
        # 2. 获取数据
        X_train, y_train, X_test, y_test = self.get_Xy()
        # 3. 进行评价
        loss, info = self.evaluate(model, X_train, y_train, X_test, y_test)  # todo : 考虑失败的情况
        # 4. 持久化
        cost_time = time() - start
        info["config_id"] = config_id
        info["status"] = "success"
        info["program_hyper_param"] = shp
        info["dict_hyper_param"] = dhp
        estimator = list(dhp.get("estimator", {"unk": ""}).keys())[0]
        info["estimator"] = estimator
        info["cost_time"] = cost_time
        self.resource_manager.insert_to_trials_db(info)
        return loss
