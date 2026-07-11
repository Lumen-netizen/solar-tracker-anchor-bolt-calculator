from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Any


SHEAR_CASE_LABELS = {
    1: "Case 1 - two nearest anchors from the shear edge resist total anchor shear Vuag with bearing in round holes",
    2: "Case 2 - two farthest anchors from the shear edge resist total anchor shear Vuag; the near-row anchors require slotted holes parallel to V to release shear",
}


TENSION_ANCHOR_COUNT = 2
SHEAR_ANCHOR_COUNT = 2
AUTO_FACTOR_KEYS = {
    "psi_ec_n",
    "psi_cp_n",
    "phi_pullout",
    "psi_ec_v",
    "psi_h_v",
    "kcp",
    "phi_pryout",
}
PSI_TO_MPA = 0.006894757293168361
ACI_MAX_CAST_IN_FC_PRIME_MPA = 10000.0 * PSI_TO_MPA
ACI_MAX_FUTA_MPA = 125000.0 * PSI_TO_MPA
ACI_MAX_ANCHOR_DIAMETER_MM = 4.0 * 25.4


@dataclass(frozen=True)
class InputSpec:
    key: str
    label_cn: str
    symbol: str
    unit: str
    default: float
    group: str
    tooltip: str
    decimals: int = 3


INPUT_SPECS: tuple[InputSpec, ...] = (
    InputSpec("plate_l", "钢板长度", "l", "mm", 370.0, "Geometry", "Base plate dimension in the moment direction.", 1),
    InputSpec("plate_b", "钢板宽度", "b", "mm", 270.0, "Geometry", "Base plate dimension perpendicular to the moment direction.", 1),
    InputSpec("da", "锚栓直径", "da", "mm", 22.0, "Geometry", "Nominal anchor bolt diameter.", 1),
    InputSpec("ase", "锚栓有效面积", "Ase", "mm2", 303.399, "Geometry", "Effective steel area used for anchor tension and shear.", 3),
    InputSpec("hef", "有效埋深", "hef", "mm", 270.0, "Geometry", "Effective embedment depth measured from the concrete surface.", 1),
    InputSpec("s1", "锚栓间距 1", "s1", "mm", 260.0, "Geometry", "Spacing between the two anchor rows in the moment direction.", 1),
    InputSpec("s2", "锚栓间距 2", "s2", "mm", 180.0, "Geometry", "Spacing between the two anchor columns perpendicular to the moment direction.", 1),
    InputSpec("pedestal_l", "基础墩长度", "L", "mm", 400.0, "Geometry", "Concrete pedestal dimension in the moment direction.", 1),
    InputSpec("pedestal_b", "基础墩宽度", "B", "mm", 400.0, "Geometry", "Concrete pedestal dimension perpendicular to the moment direction.", 1),
    InputSpec("ha", "基础墩高度", "ha", "mm", 800.0, "Geometry", "Concrete member thickness or pedestal height.", 1),
    InputSpec("eh", "弯钩端距", "eh", "mm", 95.0, "Geometry", "Distance from the inner surface of the shaft to the outer tip of a J- or L-bolt.", 1),
    InputSpec("built_up_grout_pad", "灌浆垫层", "built-up grout pad", "-", 1.0, "Geometry", "Whether built-up grout pads are used. If yes, ACI 318-19 17.7.1.2.1 applies 0.80 to Vsa.", 0),
    InputSpec("futa", "锚栓规定抗拉强度", "futa", "MPa", 355.0, "Materials", "Specified tensile strength of anchor steel.", 1),
    InputSpec("lambda_a", "轻骨料修正系数", "λa", "-", 1.0, "Materials", "Modification factor for lightweight concrete.", 3),
    InputSpec("fc_prime", "混凝土规定抗压强度", "fc'", "MPa", 24.0, "Materials", "Specified compressive strength of concrete, f'c.", 1),
    InputSpec("fc_design", "局部承压设计值", "fc", "MPa", 14.3, "Materials", "Design compressive strength used for base plate local bearing check.", 1),
    InputSpec("ec_modulus", "混凝土弹性模量", "Ec", "10^4 N/mm2", 3.0, "Materials", "Concrete elastic modulus used for the force distribution in Steel Joint Design Manual Table 8-3.", 3),
    InputSpec("es_modulus", "钢材弹性模量", "Es", "10^5 N/mm2", 2.06, "Materials", "Steel elastic modulus used for the force distribution in Steel Joint Design Manual Table 8-3.", 3),
    InputSpec("fy_tension_rebar", "抗拉配筋设计强度", "fy,N", "MPa", 300.0, "Materials", "Design strength used to estimate required tension anchor reinforcement area.", 1),
    InputSpec("fy_shear_rebar", "抗剪配筋设计强度", "fy,V", "MPa", 300.0, "Materials", "Design strength used to estimate required shear anchor reinforcement area.", 1),
    InputSpec("tension_rebar_factor", "抗拉实配钢筋放大系数", "k_As,N", "-", 1.10, "Materials", "Multiplier applied to the calculated required tension anchor reinforcement area.", 3),
    InputSpec("shear_rebar_factor", "抗剪实配钢筋放大系数", "k_As,V", "-", 1.10, "Materials", "Multiplier applied to the calculated required shear anchor reinforcement area.", 3),
    InputSpec("n", "轴力设计值", "N", "kN", 20.0, "Loads", "Positive value means downward compression at the base plate.", 2),
    InputSpec("m", "弯矩设计值", "M", "kN.m", 25.0, "Loads", "Moment may be positive or negative. The sign controls the tension anchor row; the force magnitude uses |M|/N.", 2),
    InputSpec("v", "剪力设计值", "V", "kN", 15.0, "Loads", "Positive value acts in the blue-arrow direction shown in the diagram. Negative shear is not accepted.", 2),
    InputSpec("mu", "界面摩擦系数", "μ", "-", 0.4, "Loads", "Coefficient used for friction force Vfb = mu x (Ta + N).", 3),
    InputSpec("phi_tension_steel", "钢材抗拉折减系数", "φ (for Nsa)", "-", 0.75, "Factors", "Strength reduction factor for steel tension.", 3),
    InputSpec("psi_ec_n", "抗拉偏心修正", "ψec,N", "-", 1.0, "Factors", "Modification factor for eccentricity effects in tension breakout.", 3),
    InputSpec("psi_c_n", "抗拉开裂修正", "ψc,N", "-", 1.25, "Factors", "Modification factor for cracking in tension breakout.", 3),
    InputSpec("psi_cp_n", "抗拉劈裂修正", "ψcp,N", "-", 1.0, "Factors", "Splitting factor for cast-in anchors, fixed at 1.0 by ACI 318-19 17.6.2.6.2.", 3),
    InputSpec("phi_tension_concrete", "混凝土抗拉折减系数", "φ (for Ncbg)", "-", 0.75, "Factors", "Strength reduction factor for concrete breakout in tension.", 3),
    InputSpec("psi_c_p", "拔出开裂修正", "ψc,P", "-", 1.4, "Factors", "Modification factor for pullout strength.", 3),
    InputSpec("phi_pullout", "拔出折减系数", "φ (for Npn)", "-", 0.70, "Factors", "Strength reduction factor for pullout of cast-in anchors per ACI 318-19 Table 17.5.3(c).", 3),
    InputSpec("phi_shear_steel", "钢材抗剪折减系数", "φ (for Vsa)", "-", 0.65, "Factors", "Strength reduction factor for steel shear.", 3),
    InputSpec("psi_ec_v", "抗剪偏心修正", "ψec,V", "-", 1.0, "Factors", "Modification factor for eccentricity effects in shear breakout.", 3),
    InputSpec("psi_c_v", "抗剪开裂修正", "ψc,V", "-", 1.2, "Factors", "Modification factor for cracking in shear breakout.", 3),
    InputSpec("k_stm", "抗剪锚固钢筋传力放大系数", "kSTM", "-", 1.20, "Factors", "Strut-and-tie force amplification factor for shear anchor reinforcement.", 3),
    InputSpec("psi_h_v", "厚度修正", "ψh,V", "-", 1.0, "Factors", "Modification factor for member thickness in shear breakout.", 3),
    InputSpec("phi_shear_concrete", "混凝土抗剪折减系数", "φ (for Vcbg)", "-", 0.75, "Factors", "Strength reduction factor for concrete breakout in shear.", 3),
    InputSpec("kcp", "撬出系数", "kcp", "-", 2.0, "Factors", "Coefficient for concrete pryout strength.", 3),
    InputSpec("phi_pryout", "撬出折减系数", "φ (for Vcpg)", "-", 0.70, "Factors", "Strength reduction factor for concrete pryout of cast-in anchors per ACI 318-19 Table 17.5.3(c).", 3),
)


DEFAULT_VALUES: dict[str, float] = {spec.key: spec.default for spec in INPUT_SPECS}
DEFAULT_VALUES["shear_case"] = 1.0


@dataclass(frozen=True)
class CheckResult:
    name: str
    section: str
    formula: str
    substitution: str
    demand: float | None
    capacity: float | None
    ratio: float | None
    status: str
    note: str = ""


@dataclass(frozen=True)
class AnchorInputs:
    plate_l: float = DEFAULT_VALUES["plate_l"]
    plate_b: float = DEFAULT_VALUES["plate_b"]
    futa: float = DEFAULT_VALUES["futa"]
    da: float = DEFAULT_VALUES["da"]
    ase: float = DEFAULT_VALUES["ase"]
    hef: float = DEFAULT_VALUES["hef"]
    s1: float = DEFAULT_VALUES["s1"]
    s2: float = DEFAULT_VALUES["s2"]
    pedestal_l: float = DEFAULT_VALUES["pedestal_l"]
    pedestal_b: float = DEFAULT_VALUES["pedestal_b"]
    ha: float = DEFAULT_VALUES["ha"]
    built_up_grout_pad: float = DEFAULT_VALUES["built_up_grout_pad"]
    lambda_a: float = DEFAULT_VALUES["lambda_a"]
    fc_prime: float = DEFAULT_VALUES["fc_prime"]
    fc_design: float = DEFAULT_VALUES["fc_design"]
    ec_modulus: float = DEFAULT_VALUES["ec_modulus"]
    es_modulus: float = DEFAULT_VALUES["es_modulus"]
    n: float = DEFAULT_VALUES["n"]
    m: float = DEFAULT_VALUES["m"]
    v: float = DEFAULT_VALUES["v"]
    mu: float = DEFAULT_VALUES["mu"]
    phi_tension_steel: float = DEFAULT_VALUES["phi_tension_steel"]
    psi_ec_n: float = DEFAULT_VALUES["psi_ec_n"]
    psi_c_n: float = DEFAULT_VALUES["psi_c_n"]
    psi_cp_n: float = DEFAULT_VALUES["psi_cp_n"]
    phi_tension_concrete: float = DEFAULT_VALUES["phi_tension_concrete"]
    fy_tension_rebar: float = DEFAULT_VALUES["fy_tension_rebar"]
    tension_rebar_factor: float = DEFAULT_VALUES["tension_rebar_factor"]
    eh: float = DEFAULT_VALUES["eh"]
    psi_c_p: float = DEFAULT_VALUES["psi_c_p"]
    phi_pullout: float = DEFAULT_VALUES["phi_pullout"]
    phi_shear_steel: float = DEFAULT_VALUES["phi_shear_steel"]
    shear_case: int = 1
    psi_ec_v: float = DEFAULT_VALUES["psi_ec_v"]
    psi_c_v: float = DEFAULT_VALUES["psi_c_v"]
    k_stm: float = DEFAULT_VALUES["k_stm"]
    psi_h_v: float = DEFAULT_VALUES["psi_h_v"]
    phi_shear_concrete: float = DEFAULT_VALUES["phi_shear_concrete"]
    fy_shear_rebar: float = DEFAULT_VALUES["fy_shear_rebar"]
    shear_rebar_factor: float = DEFAULT_VALUES["shear_rebar_factor"]
    kcp: float = DEFAULT_VALUES["kcp"]
    phi_pryout: float = DEFAULT_VALUES["phi_pryout"]


@dataclass(frozen=True)
class TensionBreakoutGeometry:
    ca_near: float
    ca_far: float
    ca_left: float
    ca_right: float
    close_edge_count: int
    h_eff_used: float
    h_eff_candidate: float
    h_eff_limited: bool
    projection: float
    projected_width: float
    projected_length: float
    area: float
    reference_area: float
    capped_area: float
    psi_ed: float


@dataclass(frozen=True)
class ShearBreakoutGeometry:
    ca1_actual: float
    ca1_used: float
    ca1_limited: bool
    ca2_left: float
    ca2_right: float
    projection: float
    projected_width: float
    projected_depth: float
    area: float
    reference_area: float
    capped_area: float
    critical_spacing: float
    psi_ed: float
    psi_h: float


@dataclass(frozen=True)
class AnchorResults:
    inputs: AnchorInputs
    values: dict[str, Any]
    checks: list[CheckResult]
    tension_rebar_area: float
    shear_rebar_area: float
    governing_tension_ratio: float
    governing_shear_ratio: float
    interaction_5_3: CheckResult
    overall_status: str
    warnings: list[str] = field(default_factory=list)


class CalculationError(ValueError):
    pass


def inputs_from_mapping(values: dict[str, Any]) -> AnchorInputs:
    clean: dict[str, Any] = {}
    field_names = set(AnchorInputs.__dataclass_fields__.keys())
    for key in field_names:
        if key not in values:
            continue
        if key == "shear_case":
            clean[key] = int(float(values[key]))
        elif key == "built_up_grout_pad":
            clean[key] = _to_bool_number(values[key], key)
        else:
            clean[key] = _to_float(values[key], key)
    return AnchorInputs(**clean)


def calc_tension_breakout_geometry(inputs: AnchorInputs) -> TensionBreakoutGeometry:
    """Projected concrete breakout area for the two-anchor tension row."""
    i = inputs
    ca_near = (i.pedestal_l - i.s1) / 2.0
    ca_far = ca_near + i.s1
    ca_left = (i.pedestal_b - i.s2) / 2.0
    ca_right = ca_left
    edge_distances = (ca_near, ca_far, ca_left, ca_right)

    close_edges = [edge for edge in edge_distances if edge < 1.5 * i.hef]
    h_eff_candidate = i.hef
    if len(close_edges) >= 3:
        h_eff_candidate = max(max(close_edges) / 1.5, i.s2 / 3.0)
    h_eff_used = min(i.hef, h_eff_candidate)
    h_eff_limited = h_eff_used < i.hef - 1.0e-9

    projection = 1.5 * h_eff_used
    width_left = min(ca_left, projection)
    width_right = min(ca_right, projection)
    length_near = min(ca_near, projection)
    length_far = min(ca_far, projection)
    projected_width = width_left + i.s2 + width_right
    projected_length = length_near + length_far
    area = projected_width * projected_length
    reference_area = 9.0 * h_eff_used**2
    capped_area = min(area, TENSION_ANCHOR_COUNT * reference_area)

    ca_min = min(edge_distances)
    psi_ed = 1.0
    if ca_min < projection:
        psi_ed = 0.7 + 0.3 * ca_min / projection

    return TensionBreakoutGeometry(
        ca_near=ca_near,
        ca_far=ca_far,
        ca_left=ca_left,
        ca_right=ca_right,
        close_edge_count=len(close_edges),
        h_eff_used=h_eff_used,
        h_eff_candidate=h_eff_candidate,
        h_eff_limited=h_eff_limited,
        projection=projection,
        projected_width=projected_width,
        projected_length=projected_length,
        area=area,
        reference_area=reference_area,
        capped_area=capped_area,
        psi_ed=psi_ed,
    )


def calc_shear_breakout_geometry(inputs: AnchorInputs) -> ShearBreakoutGeometry:
    """Projected concrete breakout area for the selected two-anchor shear row."""
    i = inputs
    ca1 = (i.pedestal_l - i.s1) / 2.0
    ca2 = (i.pedestal_b - i.s2) / 2.0
    ca1_actual = ca1 if i.shear_case == 1 else ca1 + i.s1
    ca1_used = ca1_actual
    if ca2 < 1.5 * ca1_actual and i.ha < 1.5 * ca1_actual:
        ca1_used = min(ca1_actual, max(ca2 / 1.5, i.ha / 1.5, i.s2 / 3.0))
    ca1_limited = ca1_used < ca1_actual - 1.0e-9

    projection = 1.5 * ca1_used
    width_left = min(ca2, projection)
    width_right = min(ca2, projection)
    projected_width = width_left + i.s2 + width_right
    projected_depth = min(i.ha, projection)
    area = projected_width * projected_depth
    reference_area = 4.5 * ca1_used**2
    capped_area = min(area, SHEAR_ANCHOR_COUNT * reference_area)

    psi_ed = 1.0
    if ca2 < projection:
        psi_ed = 0.7 + 0.3 * ca2 / projection
    psi_h = max(math.sqrt(projection / i.ha), 1.0) if i.ha < projection else 1.0

    return ShearBreakoutGeometry(
        ca1_actual=ca1_actual,
        ca1_used=ca1_used,
        ca1_limited=ca1_limited,
        ca2_left=ca2,
        ca2_right=ca2,
        projection=projection,
        projected_width=projected_width,
        projected_depth=projected_depth,
        area=area,
        reference_area=reference_area,
        capped_area=capped_area,
        critical_spacing=3.0 * ca1_used,
        psi_ed=psi_ed,
        psi_h=psi_h,
    )


def calculate_anchor(inputs: AnchorInputs) -> AnchorResults:
    i = replace(inputs, psi_cp_n=1.0, phi_pullout=0.70, phi_pryout=0.70)
    _validate_inputs(i)
    values: dict[str, Any] = {}
    warnings: list[str] = []
    checks: list[CheckResult] = []

    ca1 = (i.pedestal_l - i.s1) / 2.0
    ca2 = (i.pedestal_b - i.s2) / 2.0
    force = _manual_force_distribution(i)
    eccentricity = force["eccentricity"]
    sigma_max = force["sigma_max"]
    sigma_min = force["sigma_min"]
    compression_x = force["compression_x"]
    ta = force["total_anchor_tension"]
    friction_force = i.mu * (ta + i.n)
    nuag = ta
    vua_total = max(i.v - friction_force, 0.0)
    vua = vua_total / SHEAR_ANCHOR_COUNT
    vuag = vua_total
    nua = nuag / TENSION_ANCHOR_COUNT

    values.update(
        ca1=ca1,
        ca2=ca2,
        eccentricity=eccentricity,
        eccentricity_abs=force["eccentricity_abs"],
        tension_anchor_row=force["tension_anchor_row"],
        tension_anchor_row_label=force["tension_anchor_row_label"],
        sigma_max=sigma_max,
        sigma_min=sigma_min,
        compression_x=compression_x,
        tension_trigger=force["case_b_limit"],
        force_case=force["force_case"],
        force_case_label=force["force_case_label"],
        l1=force["l1"],
        ae_star=force["ae_star"],
        modular_ratio=force["modular_ratio"],
        case_a_limit=force["case_a_limit"],
        case_b_limit=force["case_b_limit"],
        bearing_formula=force["bearing_formula"],
        bearing_substitution=force["bearing_substitution"],
        total_anchor_tension=ta,
        friction_force=friction_force,
        nua=nua,
        nuag=nuag,
        vua=vua,
        vuag=vuag,
    )

    spacing_reference = "ACI 318-19 17.9.2 / Table 17.9.2(a)"
    checks.append(_limit_check("Minimum spacing s1", spacing_reference, "s1 >= 4da", f"{i.s1:g} >= 4 x {i.da:g}", i.s1, 4.0 * i.da, i.s1 / (4.0 * i.da), "OK" if i.s1 >= 4.0 * i.da else "NG"))
    checks.append(_limit_check("Minimum spacing s2", spacing_reference, "s2 >= 4da", f"{i.s2:g} >= 4 x {i.da:g}", i.s2, 4.0 * i.da, i.s2 / (4.0 * i.da), "OK" if i.s2 >= 4.0 * i.da else "NG"))
    checks.append(
        _limit_check(
            "Minimum member thickness ha",
            "ACI 318-19 17.9.1 / program scope",
            "Program scope: ha >= hef",
            f"ha = {i.ha:g} mm >= hef = {i.hef:g} mm",
            i.ha,
            i.hef,
            _safe_ratio(i.hef, i.ha),
            "OK" if i.ha >= i.hef else "NG",
        )
    )
    checks.append(
        _limit_check(
            "Concrete local bearing",
            "Concrete local bearing check",
            force["bearing_formula"],
            force["bearing_substitution"],
            sigma_max,
            i.fc_design,
            _safe_ratio(sigma_max, i.fc_design),
            "OK" if sigma_max <= i.fc_design else "NG",
        )
    )

    nsa = i.ase * i.futa / 1000.0
    tension_steel_ratio = _safe_ratio(nua, i.phi_tension_steel * nsa)
    checks.append(
        CheckResult(
            "Steel strength in tension",
            "ACI 318-19 17.6.1.2",
            "Nsa = Ase,N futa",
            f"Nsa = {i.ase:g} x {i.futa:g} / 1000 = {nsa:.3f} kN",
            nua,
            i.phi_tension_steel * nsa,
            tension_steel_ratio,
            _ratio_status(tension_steel_ratio),
        )
    )

    tension_geometry = calc_tension_breakout_geometry(i)
    h_eff_prime = tension_geometry.h_eff_used
    anc = tension_geometry.area
    anco = tension_geometry.reference_area
    nb = 10.0 * i.lambda_a * math.sqrt(i.fc_prime) * h_eff_prime**1.5 / 1000.0
    psi_ed_n = tension_geometry.psi_ed
    psi_ec_n = 1.0
    ncbg = (tension_geometry.capped_area / anco) * psi_ec_n * psi_ed_n * i.psi_c_n * i.psi_cp_n * nb
    tension_breakout_ratio = _safe_ratio(nuag, i.phi_tension_concrete * ncbg)
    tension_rebar_area = nuag * 1000.0 / i.fy_tension_rebar if tension_breakout_ratio > 1.0 else 0.0
    checks.append(
        CheckResult(
            "Concrete breakout strength in tension",
            "ACI 318-19 17.6.2",
            "Ncbg = (ANc/ANco) psi_ec,N psi_ed,N psi_c,N psi_cp,N Nb",
            (
                f"h'ef = {h_eff_prime:.1f} mm; ANc = {tension_geometry.projected_width:.1f} x "
                f"{tension_geometry.projected_length:.1f} = {anc:.1f} mm2; "
                f"Ncbg = min({anc:.1f}, 2 x {anco:.1f}) / {anco:.1f} x "
                f"{psi_ec_n:g} x {psi_ed_n:.3f} x {i.psi_c_n:g} x {i.psi_cp_n:g} x {nb:.3f}"
                f" = {ncbg:.3f} kN"
            ),
            nuag,
            i.phi_tension_concrete * ncbg,
            tension_breakout_ratio,
            "OK" if tension_breakout_ratio <= 1.0 else "Rebar Required",
            "Anchor group demand Nua,g is used for concrete breakout. Required tension reinforcement is reported if concrete breakout utilization exceeds 1.0.",
        )
    )

    np_basic = 0.9 * i.fc_prime * i.eh * i.da / 1000.0
    npn = i.psi_c_p * np_basic
    pullout_ratio = _safe_ratio(nua, i.phi_pullout * npn)
    checks.append(
        CheckResult(
            "Pullout strength in tension",
            "ACI 318-19 17.6.3",
            "Npn = psi_c,P Np; Np = 0.9 fc' eh da",
            f"Npn = {i.psi_c_p:g} x 0.9 x {i.fc_prime:g} x {i.eh:g} x {i.da:g} / 1000 = {npn:.3f} kN",
            nua,
            i.phi_pullout * npn,
            pullout_ratio,
            _ratio_status(pullout_ratio),
        )
    )

    shear_required = vua > 1.0e-9
    shear_transfer_ratio = _safe_ratio(i.v, friction_force) if friction_force > 0.0 else None
    checks.append(
        CheckResult(
            "Anchor shear demand after friction",
            "Load transfer model",
            "Vua = max((V - Vfb) / 2, 0); Vua,g = 2Vua; Vfb = mu(Ta + N)",
            f"Vfb = {friction_force:.3f} kN; V = {i.v:.3f} kN; Vua = {vua:.3f} kN; Vua,g = {vuag:.3f} kN",
            i.v,
            friction_force,
            shear_transfer_ratio,
            "Required" if shear_required else "Not Required",
            "If Vfb >= V, interface friction is sufficient and anchor shear strength checks are not required.",
        )
    )

    grout_factor = 0.8 if i.built_up_grout_pad >= 0.5 else 1.0
    vsa = grout_factor * 0.6 * i.ase * i.futa / 1000.0
    shear_steel_ratio = 0.0
    shear_breakout_ratio = 0.0
    pryout_ratio = 0.0
    shear_rebar_area = 0.0

    shear_geometry = calc_shear_breakout_geometry(i)
    shear_ca1_actual = shear_geometry.ca1_actual
    shear_ca1 = shear_geometry.ca1_used
    critical_spacing = shear_geometry.critical_spacing
    avc = shear_geometry.area
    avco = shear_geometry.reference_area
    load_bearing_length = min(i.hef, 8.0 * i.da)
    vb_1 = 0.6 * (load_bearing_length / i.da) ** 0.2 * math.sqrt(i.da) * i.lambda_a * math.sqrt(i.fc_prime) * shear_ca1**1.5 / 1000.0
    vb_2 = 3.7 * i.lambda_a * math.sqrt(i.fc_prime) * shear_ca1**1.5 / 1000.0
    vb = min(vb_1, vb_2)
    psi_ec_v = 1.0
    psi_ed_v = shear_geometry.psi_ed
    psi_h_v = shear_geometry.psi_h
    vcbg = (shear_geometry.capped_area / avco) * psi_ec_v * psi_ed_v * i.psi_c_v * psi_h_v * vb
    kcp = 1.0 if i.hef < 63.5 else 2.0
    vcpg = kcp * ncbg
    if shear_required:
        shear_steel_ratio = _safe_ratio(vua, i.phi_shear_steel * vsa)
        checks.append(
            CheckResult(
                "Steel strength in shear",
                "ACI 318-19 17.7.1.2",
                "Vsa = kg x 0.6 Ase,V futa",
                f"Vsa = {grout_factor:g} x 0.6 x {i.ase:g} x {i.futa:g} / 1000 = {vsa:.3f} kN",
                vua,
                i.phi_shear_steel * vsa,
                shear_steel_ratio,
                _ratio_status(shear_steel_ratio),
                "kg = 0.80 when built-up grout pads are used; otherwise kg = 1.00.",
            )
        )
        shear_breakout_ratio = _safe_ratio(vuag, i.phi_shear_concrete * vcbg)
        shear_rebar_design_force = i.k_stm * vuag
        shear_rebar_area = shear_rebar_design_force * 1000.0 / i.fy_shear_rebar if shear_breakout_ratio > 1.0 else 0.0
        checks.append(
            CheckResult(
                "Concrete breakout strength in shear",
                "ACI 318-19 17.7.2",
                "Vcbg = (AVc/AVco) psi_ec,V psi_ed,V psi_c,V psi_h,V Vb",
                (
                    f"ca1 = {shear_ca1:.1f} mm; AVc = {shear_geometry.projected_width:.1f} x "
                    f"{shear_geometry.projected_depth:.1f} = {avc:.1f} mm2; "
                    f"Vcbg = min({avc:.1f}, 2 x {avco:.1f}) / {avco:.1f} x "
                    f"{psi_ec_v:g} x {psi_ed_v:.3f} x {i.psi_c_v:g} x {psi_h_v:.3f} x {vb:.3f}"
                    f" = {vcbg:.3f} kN"
                ),
                vuag,
                i.phi_shear_concrete * vcbg,
                shear_breakout_ratio,
                "OK" if shear_breakout_ratio <= 1.0 else "Rebar Required",
                (
                    f"{SHEAR_CASE_LABELS[i.shear_case]}. Anchor group demand Vua,g is used. "
                    f"If anchor reinforcement is required, Tu,STM = kSTM x Vua,g = "
                    f"{i.k_stm:.3f} x {vuag:.3f} = {shear_rebar_design_force:.3f} kN."
                ),
            )
        )
        pryout_ratio = _safe_ratio(vuag, i.phi_pryout * vcpg)
        checks.append(
            CheckResult(
                "Concrete pryout strength in shear",
                "ACI 318-19 17.7.3",
                "Vcpg = kcp Ncpg",
                f"Vcpg = {kcp:g} x {ncbg:.3f} = {vcpg:.3f} kN",
                vuag,
                i.phi_pryout * vcpg,
                pryout_ratio,
                _ratio_status(pryout_ratio),
            )
        )

    tension_rebar_provided_area = tension_rebar_area * i.tension_rebar_factor
    shear_rebar_design_force = i.k_stm * vuag if shear_rebar_area > 0.0 else 0.0
    shear_rebar_provided_area = shear_rebar_area * i.shear_rebar_factor
    tension_rebar_strength = tension_rebar_provided_area * i.fy_tension_rebar / 1000.0
    shear_rebar_strength = shear_rebar_provided_area * i.fy_shear_rebar / 1000.0
    tension_breakout_interaction_ratio = _safe_ratio(nuag, tension_rebar_strength) if tension_rebar_area > 0.0 else tension_breakout_ratio
    shear_breakout_interaction_ratio = _safe_ratio(shear_rebar_design_force, shear_rebar_strength) if shear_rebar_area > 0.0 else shear_breakout_ratio
    tension_ratio_for_interaction = max(tension_steel_ratio, tension_breakout_interaction_ratio, pullout_ratio)
    shear_ratio_for_interaction = max(shear_steel_ratio, shear_breakout_interaction_ratio, pryout_ratio)
    shear_resisting_row = "bottom" if i.shear_case == 1 else "top"
    tension_anchor_row = str(force["tension_anchor_row"])
    same_anchor_group_for_interaction = shear_resisting_row == tension_anchor_row
    if nua <= 0.0 or not shear_required:
        interaction_value: float | None = None
        interaction_5_3 = CheckResult(
            "Tension-shear interaction",
            "ACI 318-19 17.8.1",
            "Tension-shear interaction applies only when both tension and anchor shear are present",
            f"eta_N = {tension_ratio_for_interaction:.3f}; eta_V = {shear_ratio_for_interaction:.3f}",
            None,
            None,
            None,
            "Not Applicable",
            "Interaction is not applicable because anchor shear demand after friction is zero.",
        )
    elif not same_anchor_group_for_interaction:
        interaction_value = None
        interaction_5_3 = CheckResult(
            "Tension-shear interaction",
            "ACI 318-19 17.8.1",
            "Tension-shear interaction applies to anchors or anchor groups resisting both tension and shear",
            (
                f"Case {i.shear_case}: shear row = {shear_resisting_row}; "
                f"tension row = {tension_anchor_row}; "
                f"eta_N = {tension_ratio_for_interaction:.3f}; eta_V = {shear_ratio_for_interaction:.3f}"
            ),
            None,
            None,
            None,
            "Not Applicable",
            "Interaction is not applicable because the shear-resisting row and the tension row are different anchor rows.",
        )
    elif tension_ratio_for_interaction <= 0.2 or shear_ratio_for_interaction <= 0.2:
        interaction_value = None
        controlling_small_ratio = min(tension_ratio_for_interaction, shear_ratio_for_interaction)
        interaction_5_3 = CheckResult(
            "Tension-shear interaction",
            "ACI 318-19 17.8.2",
            "Interaction may be neglected if Nua/(phi Nn) <= 0.2 or Vua/(phi Vn) <= 0.2",
            (
                f"eta_N = {tension_ratio_for_interaction:.3f}; eta_V = {shear_ratio_for_interaction:.3f}; "
                f"min = {controlling_small_ratio:.3f} <= 0.2"
            ),
            None,
            None,
            None,
            "OK",
            "Interaction is permitted to be neglected by ACI 318-19 17.8.2.",
        )
    else:
        interaction_value = tension_ratio_for_interaction + shear_ratio_for_interaction
        interaction_op = "<=" if interaction_value <= 1.2 else ">"
        interaction_5_3 = CheckResult(
            "Tension-shear interaction",
            "ACI 318-19 17.8.3",
            "Nua/(phi Nn) + Vua/(phi Vn) <= 1.2",
            f"{tension_ratio_for_interaction:.3f} + {shear_ratio_for_interaction:.3f} = {interaction_value:.3f} {interaction_op} 1.2",
            None,
            None,
            interaction_value / 1.2,
            "OK" if interaction_value <= 1.2 else "NG",
        )

    values.update(
        nsa=nsa,
        h_eff_prime=h_eff_prime,
        tension_h_eff_candidate=tension_geometry.h_eff_candidate,
        tension_h_eff_limited=tension_geometry.h_eff_limited,
        tension_close_edge_count=tension_geometry.close_edge_count,
        tension_ca_near=tension_geometry.ca_near,
        tension_ca_far=tension_geometry.ca_far,
        tension_ca_left=tension_geometry.ca_left,
        tension_ca_right=tension_geometry.ca_right,
        tension_projection=tension_geometry.projection,
        tension_projected_width=tension_geometry.projected_width,
        tension_projected_length=tension_geometry.projected_length,
        tension_capped_area=tension_geometry.capped_area,
        anc=anc,
        anco=anco,
        nb=nb,
        psi_ed_n=psi_ed_n,
        ncbg=ncbg,
        np_basic=np_basic,
        npn=npn,
        grout_factor=grout_factor,
        vsa=vsa,
        critical_spacing=critical_spacing,
        shear_ca1_actual=shear_ca1_actual,
        shear_ca1=shear_ca1,
        shear_ca1_limited=shear_geometry.ca1_limited,
        shear_projection=shear_geometry.projection,
        shear_projected_width=shear_geometry.projected_width,
        shear_projected_depth=shear_geometry.projected_depth,
        shear_capped_area=shear_geometry.capped_area,
        avc=avc,
        avco=avco,
        load_bearing_length=load_bearing_length,
        vb=vb,
        psi_ec_n=psi_ec_n,
        psi_cp_n=i.psi_cp_n,
        phi_pullout=i.phi_pullout,
        psi_ec_v=psi_ec_v,
        psi_ed_v=psi_ed_v,
        psi_h_v=psi_h_v,
        kcp=kcp,
        phi_pryout=i.phi_pryout,
        vcbg=vcbg,
        vcpg=vcpg,
        tension_rebar_provided_area=tension_rebar_provided_area,
        shear_rebar_provided_area=shear_rebar_provided_area,
        k_stm=i.k_stm,
        shear_rebar_design_force=shear_rebar_design_force,
        tension_rebar_strength=tension_rebar_strength,
        shear_rebar_strength=shear_rebar_strength,
        tension_breakout_interaction_ratio=tension_breakout_interaction_ratio,
        shear_breakout_interaction_ratio=shear_breakout_interaction_ratio,
        shear_resisting_row=shear_resisting_row,
        interaction_same_anchor_group=same_anchor_group_for_interaction,
        interaction_applicable=(nua > 0.0 and shear_required and same_anchor_group_for_interaction),
        interaction_sum=interaction_value,
        interaction_limit=1.2,
    )

    all_statuses = [check.status for check in checks] + [interaction_5_3.status]
    if any(status == "NG" for status in all_statuses):
        overall_status = "NG"
    elif any(status == "Rebar Required" for status in all_statuses):
        overall_status = "Rebar Required"
    else:
        overall_status = "OK"

    if not shear_required:
        warnings.append("The applied shear is fully resisted by friction in the load-transfer model; anchor shear demand is zero.")

    effective_inputs = replace(i, psi_ec_n=psi_ec_n, psi_ec_v=psi_ec_v, psi_h_v=psi_h_v, kcp=kcp)

    return AnchorResults(
        inputs=effective_inputs,
        values=values,
        checks=checks,
        tension_rebar_area=tension_rebar_area,
        shear_rebar_area=shear_rebar_area,
        governing_tension_ratio=tension_ratio_for_interaction,
        governing_shear_ratio=shear_ratio_for_interaction,
        interaction_5_3=interaction_5_3,
        overall_status=overall_status,
        warnings=warnings,
    )


def _manual_force_distribution(i: AnchorInputs) -> dict[str, Any]:
    """Force distribution per Steel Structure Joint Design Manual, 4th ed., Table 8-3."""
    plate_l = i.plate_l
    plate_b = i.plate_b
    l1 = (plate_l - i.s1) / 2.0
    if l1 <= 0:
        raise CalculationError("Base plate length l must be greater than anchor spacing s1 for the force distribution model.")

    eccentricity_signed = i.m / i.n * 1000.0
    eccentricity = abs(eccentricity_signed)
    tension_row = "top" if i.m >= 0.0 else "bottom"
    tension_row_label = "Top anchor row" if tension_row == "top" else "Bottom anchor row"
    ae_star = TENSION_ANCHOR_COUNT * i.ase
    ec = i.ec_modulus * 10_000.0
    es = i.es_modulus * 100_000.0
    modular_ratio = _safe_div(es, ec, "modular ratio Es/Ec")
    case_a_limit = plate_l / 6.0
    case_b_limit = case_a_limit + l1 / 3.0

    if eccentricity <= case_a_limit + 1.0e-9:
        force_case = "a"
        force_case_label = "Case a: |e| <= l/6, full base plate compression"
        compression_x = plate_l
        sigma_max = i.n * 1000.0 / (plate_l * plate_b) * (1.0 + 6.0 * eccentricity / plate_l)
        sigma_min = i.n * 1000.0 / (plate_l * plate_b) * (1.0 - 6.0 * eccentricity / plate_l)
        ta = 0.0
        bearing_formula = "sigma_c = N/(l b)(1 + 6e/l) <= fc"
        bearing_substitution = (
            f"{i.n:g} x 1000 / ({plate_l:g} x {plate_b:g}) x "
            f"(1 + 6 x {eccentricity:.1f} / {plate_l:g}) = {sigma_max:.3f} <= {i.fc_design:g}"
        )
    elif eccentricity <= case_b_limit + 1.0e-9:
        force_case = "b"
        force_case_label = "Case b: l/6 < |e| <= l/6 + l1/3, triangular compression without anchor tension"
        compression_x = 3.0 * (plate_l / 2.0 - eccentricity)
        if compression_x <= 0:
            raise CalculationError("Compression depth became non-positive in force distribution case b.")
        sigma_max = 2.0 * i.n * 1000.0 / (plate_b * compression_x)
        sigma_min = 0.0
        ta = 0.0
        bearing_formula = "sigma_c = 2N/[3b(l/2 - e)] <= fc"
        bearing_substitution = (
            f"2 x {i.n:g} x 1000 / (3 x {plate_b:g} x ({plate_l:g}/2 - {eccentricity:.1f})) "
            f"= {sigma_max:.3f} <= {i.fc_design:g}"
        )
    else:
        force_case = "c"
        force_case_label = "Case c: |e| > l/6 + l1/3, anchor tension with partial compression"
        compression_x = _solve_manual_compression_depth(
            eccentricity=eccentricity,
            plate_l=plate_l,
            plate_b=plate_b,
            l1=l1,
            ae_star=ae_star,
            modular_ratio=modular_ratio,
        )
        lever = plate_l - l1 - compression_x / 3.0
        if lever <= 0:
            raise CalculationError("Lever arm became non-positive in force distribution case c.")
        ta = i.n * (eccentricity - plate_l / 2.0 + compression_x / 3.0) / lever
        sigma_max = (
            2.0
            * i.n
            * 1000.0
            * (eccentricity + plate_l / 2.0 - l1)
            / (plate_b * compression_x * lever)
        )
        sigma_min = 0.0
        bearing_formula = "sigma_c = 2N(e + l/2 - l1) / [b xn(l - l1 - xn/3)] <= fc"
        bearing_substitution = (
            f"2 x {i.n:g} x 1000 x ({eccentricity:.1f} + {plate_l:g}/2 - {l1:.1f}) / "
            f"({plate_b:g} x {compression_x:.3f} x ({plate_l:g} - {l1:.1f} - {compression_x:.3f}/3)) "
            f"= {sigma_max:.3f} <= {i.fc_design:g}"
        )

    return {
        "force_case": force_case,
        "force_case_label": force_case_label,
        "eccentricity": eccentricity_signed,
        "eccentricity_abs": eccentricity,
        "tension_anchor_row": tension_row,
        "tension_anchor_row_label": tension_row_label,
        "sigma_max": sigma_max,
        "sigma_min": sigma_min,
        "compression_x": compression_x,
        "total_anchor_tension": ta,
        "l1": l1,
        "ae_star": ae_star,
        "modular_ratio": modular_ratio,
        "case_a_limit": case_a_limit,
        "case_b_limit": case_b_limit,
        "bearing_formula": bearing_formula,
        "bearing_substitution": bearing_substitution,
    }


def _solve_manual_compression_depth(
    *,
    eccentricity: float,
    plate_l: float,
    plate_b: float,
    l1: float,
    ae_star: float,
    modular_ratio: float,
) -> float:
    upper = plate_l - l1
    if upper <= 0:
        raise CalculationError("Invalid force distribution geometry: l - l1 must be positive.")
    c = 6.0 * modular_ratio * ae_star / plate_b * (eccentricity + plate_l / 2.0 - l1)

    def f(x: float) -> float:
        return x**3 + 3.0 * (eccentricity - plate_l / 2.0) * x**2 + c * x - c * upper

    low = 0.0
    high = upper
    f_low = f(low)
    f_high = f(high)
    if f_low > 0 or f_high < 0:
        raise CalculationError("Unable to bracket xn for Steel Joint Design Manual Eq. 8-158.")

    for _ in range(120):
        mid = (low + high) / 2.0
        f_mid = f(mid)
        if abs(f_mid) < 1.0e-9 or (high - low) < 1.0e-9:
            return mid
        if f_mid > 0:
            high = mid
        else:
            low = mid
    return (low + high) / 2.0


def _validate_inputs(i: AnchorInputs) -> None:
    positive_fields = [
        "plate_l",
        "plate_b",
        "futa",
        "da",
        "ase",
        "hef",
        "s1",
        "s2",
        "pedestal_l",
        "pedestal_b",
        "ha",
        "lambda_a",
        "fc_prime",
        "fc_design",
        "ec_modulus",
        "es_modulus",
        "n",
        "fy_tension_rebar",
        "tension_rebar_factor",
        "eh",
        "fy_shear_rebar",
        "shear_rebar_factor",
        "k_stm",
    ]
    for field_name in positive_fields:
        if getattr(i, field_name) <= 0:
            raise CalculationError(f"{field_name} must be greater than 0.")
    nonnegative_fields = ["v", "mu"]
    for field_name in nonnegative_fields:
        if getattr(i, field_name) < 0:
            raise CalculationError(f"{field_name} must not be negative. Use the diagram for sign convention.")
    if i.k_stm < 1.0:
        raise CalculationError("kSTM must be at least 1.0 for the shear anchor reinforcement load-transfer model.")
    if i.pedestal_l <= i.s1:
        raise CalculationError("Pedestal length L must be greater than anchor spacing s1.")
    if i.pedestal_b <= i.s2:
        raise CalculationError("Pedestal width B must be greater than anchor spacing s2.")
    if i.fc_prime > ACI_MAX_CAST_IN_FC_PRIME_MPA:
        raise CalculationError(
            "ACI 318-19 17.3.1 limits f'c used for cast-in anchor calculations to "
            f"10000 psi ({ACI_MAX_CAST_IN_FC_PRIME_MPA:.1f} MPa)."
        )
    if i.futa > ACI_MAX_FUTA_MPA:
        raise CalculationError(
            "ACI 318-19 17.6.1.2 and 17.7.1.2 limit futa used for calculation to "
            f"125 ksi ({ACI_MAX_FUTA_MPA:.1f} MPa). Also confirm futa <= 1.9fya because fya is not an input."
        )
    if i.da > ACI_MAX_ANCHOR_DIAMETER_MM:
        raise CalculationError(
            "ACI 318-19 17.3.2 concrete breakout provisions used by this program apply to "
            f"anchor diameter da <= 4 in. ({ACI_MAX_ANCHOR_DIAMETER_MM:.1f} mm)."
        )
    if not (3.0 * i.da <= i.eh <= 4.5 * i.da):
        raise CalculationError("For the J- or L-bolt pullout formula in ACI 318-19 17.6.3.2.2(b), eh must satisfy 3da <= eh <= 4.5da.")
    if i.shear_case not in (1, 2):
        raise CalculationError("shear_case must be 1 or 2.")
    if i.built_up_grout_pad not in (0.0, 1.0):
        raise CalculationError("built_up_grout_pad must be Yes or No.")
    for field_name, value in i.__dict__.items():
        if isinstance(value, float) and not math.isfinite(value):
            raise CalculationError(f"{field_name} must be finite.")


def _to_float(value: Any, key: str) -> float:
    try:
        number = float(str(value).strip())
    except Exception as exc:
        raise CalculationError(f"{key} must be a number.") from exc
    if not math.isfinite(number):
        raise CalculationError(f"{key} must be finite.")
    return number


def _to_bool_number(value: Any, key: str) -> float:
    text = str(value).strip().lower()
    if text in {"1", "1.0", "yes", "y", "true", "有", "有 / yes"}:
        return 1.0
    if text in {"0", "0.0", "no", "n", "false", "无", "无 / no"}:
        return 0.0
    try:
        number = float(text)
    except Exception as exc:
        raise CalculationError(f"{key} must be Yes or No.") from exc
    if number in (0.0, 1.0):
        return number
    raise CalculationError(f"{key} must be Yes or No.")


def _safe_div(numerator: float, denominator: float, label: str) -> float:
    if abs(denominator) < 1e-12:
        raise CalculationError(f"Division by zero while calculating {label}.")
    return numerator / denominator


def _safe_ratio(demand: float, capacity: float) -> float:
    if capacity <= 0:
        return math.inf
    return demand / capacity


def _ratio_status(ratio: float) -> str:
    return "OK" if ratio <= 1.0 else "NG"


def _limit_check(
    name: str,
    section: str,
    formula: str,
    substitution: str,
    demand: float | None,
    capacity: float | None,
    ratio: float | None,
    status: str,
) -> CheckResult:
    return CheckResult(name, section, formula, substitution, demand, capacity, ratio, status)
