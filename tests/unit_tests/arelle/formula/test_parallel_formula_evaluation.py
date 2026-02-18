from unittest.mock import MagicMock, patch
import pytest

from arelle.ModelFormulaObject import FormulaOptions
from arelle.formula.XPathContext import XPathContext


class TestFormulaOptionsParallel:
    def test_parallel_formula_evaluation_default_false(self):
        options = FormulaOptions()
        assert options.parallelFormulaEvaluation is False

    def test_parallel_formula_evaluation_set_true(self):
        options = FormulaOptions()
        options.parallelFormulaEvaluation = True
        assert options.parallelFormulaEvaluation is True

    def test_parallel_formula_evaluation_from_saved_values(self):
        options = FormulaOptions(savedValues={"parallelFormulaEvaluation": True})
        assert options.parallelFormulaEvaluation is True


class TestXPathContextCopyForFormulaEvaluation:
    def _make_xp_ctx(self):
        modelXbrl = MagicMock()
        modelXbrl.modelManager.formulaOptions = FormulaOptions()
        inputXbrlInstance = MagicMock()
        inputXbrlInstance.modelXbrl = modelXbrl
        sourceElement = MagicMock()
        xpCtx = XPathContext(modelXbrl, inputXbrlInstance, sourceElement)
        return xpCtx

    def test_copy_shares_model_xbrl(self):
        xpCtx = self._make_xp_ctx()
        copy = xpCtx.copyForFormulaEvaluation()
        assert copy.modelXbrl is xpCtx.modelXbrl

    def test_copy_shares_input_instance(self):
        xpCtx = self._make_xp_ctx()
        copy = xpCtx.copyForFormulaEvaluation()
        assert copy.inputXbrlInstance is xpCtx.inputXbrlInstance

    def test_copy_has_independent_in_scope_vars(self):
        xpCtx = self._make_xp_ctx()
        xpCtx.inScopeVars["test_key"] = "test_value"
        copy = xpCtx.copyForFormulaEvaluation()
        assert copy.inScopeVars["test_key"] == "test_value"
        # Modifying copy should not affect original
        copy.inScopeVars["new_key"] = "new_value"
        assert "new_key" not in xpCtx.inScopeVars

    def test_copy_preserves_dimension_aspects(self):
        xpCtx = self._make_xp_ctx()
        xpCtx.defaultDimensionAspects = {"dim1", "dim2"}
        xpCtx.dimensionsAspectUniverse = {"dim1", "dim2", "dim3"}
        copy = xpCtx.copyForFormulaEvaluation()
        assert copy.defaultDimensionAspects == {"dim1", "dim2"}
        assert copy.dimensionsAspectUniverse == {"dim1", "dim2", "dim3"}

    def test_copy_preserves_runtime_exceeded(self):
        xpCtx = self._make_xp_ctx()
        xpCtx.isRunTimeExceeded = True
        copy = xpCtx.copyForFormulaEvaluation()
        assert copy.isRunTimeExceeded is True

    def test_copy_preserves_custom_functions(self):
        xpCtx = self._make_xp_ctx()
        custom_fn = MagicMock()
        xpCtx.customFunctions["my_func"] = custom_fn
        copy = xpCtx.copyForFormulaEvaluation()
        assert copy.customFunctions["my_func"] is custom_fn

    def test_copy_has_independent_fact_aspects_cache(self):
        import uuid
        xpCtx = self._make_xp_ctx()
        copy = xpCtx.copyForFormulaEvaluation()
        # Each copy should have its own cache instance
        assert copy.factAspectsCache is not xpCtx.factAspectsCache
        # Verify modifications to one cache don't affect the other
        class _Fact:
            def __init__(self):
                self.uniqueUUID = uuid.uuid4()
        f1, f2 = _Fact(), _Fact()
        xpCtx.factAspectsCache.cacheMatch(f1, f2, "aspect")
        assert xpCtx.factAspectsCache.evaluations(f1, f2) == {"aspect": True}
        assert copy.factAspectsCache.evaluations(f1, f2) is None


class TestEligibleVariableSet:
    def test_is_eligible_no_scope_no_run_ids(self):
        from arelle.formula.ValidateFormula import _isEligibleVariableSet
        val = MagicMock()
        val.modelXbrl.relationshipSet.return_value.toModelObject.return_value = []
        mvs = MagicMock()
        mvs.id = "test_id"
        assert _isEligibleVariableSet(val, mvs, None) is True

    def test_not_eligible_has_scope(self):
        from arelle.formula.ValidateFormula import _isEligibleVariableSet
        val = MagicMock()
        val.modelXbrl.relationshipSet.return_value.toModelObject.return_value = [MagicMock()]
        mvs = MagicMock()
        assert _isEligibleVariableSet(val, mvs, None) is False
