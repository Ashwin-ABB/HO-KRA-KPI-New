from kra_kpi.kra.doctype.ho_traffic_light_settings.ho_traffic_light_settings import (
	ensure_defaults as ho_traffic_light_defaults,
)
from kra_kpi.kra.doctype.internal_feedback_settings.internal_feedback_settings import (
	ensure_defaults as internal_feedback_defaults,
)


def ensure_defaults():
	internal_feedback_defaults()
	ho_traffic_light_defaults()
