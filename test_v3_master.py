import unittest

from test_data_quality_engine import TestDataQualityEngine
from test_market_regime_v3 import TestMarketRegimeV3Engine
from test_momentum_intelligence_v3 import TestMomentumIntelligenceV3Engine
from test_intraday_precision_v3 import TestIntradayPrecisionV3Engine
from test_options_engine_v3 import TestOptionsEngineV3
from test_mcx_event_engine import TestMCXEventEngine
from test_institutional_flow_v3 import TestInstitutionalFlowV3Engine
from test_risk_engine_v3 import TestRiskEngineV3
from test_trade_quality_gate import TestTradeQualityGateEngine
from test_ai_explanation_engine import TestAIExplanationEngine
from test_telegram_bot_v3 import TestTelegramBotV3Engine
from test_master_acceptance import TestPhase10BrokerAndMasterAcceptance

if __name__ == '__main__':
    print("==========================================================================")
    print("   MARKET MENTOR AI V3.0 — MASTER ZERO-REGRESSION TEST SUITE             ")
    print("==========================================================================")
    unittest.main()
