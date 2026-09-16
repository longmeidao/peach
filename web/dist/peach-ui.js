import { MEDIA_SOURCE_ICONS as e, checkboxHtml as t, emptyStateHtml as n, loadingDotsHtml as r, moveGlidePane as i, noteHtml as a, selectFieldHtml as o, selectOptionIconHtml as s, setActionBusy as c, wireCollapse as l, wireSelectField as u } from "/js/ui-components.js";
import { esc as d, icon as f, requestErrorMessage as p } from "/js/core.js";
//#region src/sort-preferences.ts
function m(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/number-setting.ts
var h = {
	loginDaysSetting: {
		min: 1,
		max: 365,
		unit: "天",
		fallback: 30
	},
	batchSizeSetting: {
		min: 1,
		max: 200,
		unit: "个",
		fallback: 60
	},
	hoverDelaySetting: {
		min: 1,
		max: 60,
		unit: "秒",
		optional: !0,
		fallback: 5
	},
	seekSecondsSetting: {
		min: 1,
		max: 300,
		unit: "秒",
		fallback: 10
	},
	relatedLimitSetting: {
		min: 1,
		max: 60,
		unit: "个",
		optional: !0,
		fallback: 20
	},
	searchHistoryLimitSetting: {
		min: 1,
		max: 50,
		unit: "条",
		optional: !0,
		fallback: 10
	},
	followScheduleSetting: {
		min: 15,
		max: 10080,
		unit: "分钟",
		optional: !0,
		fallback: 60
	}
};
function g(e, t, n, r) {
	return Number.isInteger(e) && e >= t && e <= n ? e : r;
}
function _(e, t, n) {
	let r = e.querySelector("input[type=number]"), i = e.querySelector("[role=switch]"), a = e.querySelector(".board-number-fields");
	r && (r.disabled = n, t !== null && t > 0 && (r.value = String(t))), i && (i.disabled = n, t !== null && (i.checked = t > 0)), a && t !== null && (a.hidden = t === 0);
}
function v(e, t, n, r, i) {
	let a = h[t];
	if (!a) return !1;
	let { min: o, max: s, unit: c, optional: l, fallback: u } = a, d = `peach.number.${t}`, f = g(Number(localStorage.getItem(d)), o, s, r > 0 ? r : u), p = document.createElement("div");
	p.className = "board-optional-number";
	let m = document.createElement("div");
	m.className = "board-number-fields", m.hidden = !!l && r === 0;
	let _ = document.createElement("div");
	_.className = "board-number-control";
	let v = document.createElement("input");
	v.type = "number", v.className = "geist-input", v.min = String(o), v.max = String(s), v.step = "1", v.value = String(r > 0 ? r : f), v.setAttribute("aria-label", n);
	let y = document.createElement("span");
	y.textContent = c, y.setAttribute("aria-hidden", "true");
	let b = document.createElement("small");
	b.id = `${t}-error`, b.className = "board-number-error", b.setAttribute("role", "status"), b.hidden = !0, v.setAttribute("aria-describedby", b.id), _.append(v, y), m.append(_, b), p.append(m), e.replaceChildren(p);
	let x = () => {
		v.removeAttribute("aria-invalid"), b.hidden = !0, b.textContent = "";
	}, S = () => {
		if (!v.value || !v.checkValidity()) {
			v.setAttribute("aria-invalid", "true"), b.textContent = `请输入 ${o}–${s} 的整数（${c}）`, b.hidden = !1;
			return;
		}
		x(), f = Number(v.value), localStorage.setItem(d, String(f)), i(v.value);
	};
	if (v.addEventListener("change", S), v.addEventListener("keydown", (e) => {
		e.key === "Enter" && (e.preventDefault(), S());
	}), v.addEventListener("input", () => {
		v.value && v.checkValidity() && x();
	}), l) {
		let e = document.createElement("input");
		e.type = "checkbox", e.className = "ptoggle", e.setAttribute("role", "switch"), e.setAttribute("aria-label", `启用${n}`), e.checked = r > 0, e.onchange = () => {
			x(), m.hidden = !e.checked, e.checked ? (v.value = String(f), S()) : (v.value && v.checkValidity() && (f = Number(v.value)), localStorage.setItem(d, String(f)), i("0"));
		}, p.prepend(e);
	}
	return !0;
}
//#endregion
//#region src/board-controls.ts
function y(e) {
	let t = Number(e.min) || 0, n = Number(e.max) || 100, r = Number(e.value), i = n > t ? Math.max(0, Math.min(100, (r - t) / (n - t) * 100)) : 0;
	e.style.setProperty("--board-range-value", `${i}%`);
	let a = e.closest(".dual-range");
	if (!a) return;
	let o = e.id === "durMax" ? "max" : "min", s = a.querySelector(`[data-range-end="${o}"]`);
	s || (s = document.createElement("output"), s.className = "board-range-tip", s.dataset.rangeEnd = o, s.setAttribute("aria-hidden", "true"), a.append(s)), s.textContent = r >= n && o === "max" ? "不限" : `${r} 分钟`, s.style.left = `${i}%`, s.style.setProperty("--range-tip-shift", "0px");
	let c = a.getBoundingClientRect(), l = s.getBoundingClientRect(), u = l.right > c.right ? c.right - l.right : l.left < c.left ? c.left - l.left : 0;
	u && s.style.setProperty("--range-tip-shift", `${Math.round(u)}px`), a.querySelectorAll(".board-range-tip").forEach((e) => e.toggleAttribute("data-range-active", e === s));
}
function b() {
	let e = (e) => {
		e.querySelectorAll("input[type=range]").forEach(y), w(e), S(e);
	};
	e(document), new MutationObserver((t) => {
		for (let n of t) for (let t of n.addedNodes) t instanceof Element && (t.matches("input[type=range]") && y(t), e(t));
	}).observe(document.body, {
		subtree: !0,
		childList: !0
	}), document.addEventListener("input", (e) => {
		e.target instanceof HTMLInputElement && e.target.type === "range" && y(e.target);
	});
	let t = document.createElement("div");
	t.className = "board-tooltip", t.id = "board-control-tooltip", t.role = "tooltip", t.hidden = !0, document.body.append(t);
	let n = null, r = "", i = null, a, o = () => {
		clearTimeout(a), t.hidden = !0, n && (n.hasAttribute("title") || (n.title = r), i === null ? n.removeAttribute("aria-describedby") : n.setAttribute("aria-describedby", i)), n = null;
	}, s = (e, s) => {
		let c = e instanceof Element ? e.closest("[title]") : null;
		!c || c === n || c.closest(".vjs-control") || !c.title.trim() || (o(), n = c, r = c.title, i = c.getAttribute("aria-describedby"), c.removeAttribute("title"), a = setTimeout(() => {
			if (n !== c || !c.isConnected) return;
			t.textContent = r, t.hidden = !1;
			let e = c.getBoundingClientRect(), a = t.getBoundingClientRect();
			t.style.left = `${Math.max(8, Math.min(innerWidth - a.width - 8, e.left + (e.width - a.width) / 2))}px`, t.style.top = `${e.top >= a.height + 16 ? e.top - a.height - 8 : Math.min(innerHeight - a.height - 8, e.bottom + 8)}px`, c.setAttribute("aria-describedby", [i, t.id].filter(Boolean).join(" "));
		}, s));
	};
	document.addEventListener("pointerover", (e) => s(e.target, 400)), document.addEventListener("pointerout", (e) => {
		n && !n.contains(e.relatedTarget) && o();
	}), document.addEventListener("focusin", (e) => s(e.target, 0)), document.addEventListener("focusout", o), document.addEventListener("keydown", (e) => {
		e.key === "Escape" && o();
	}), document.addEventListener("scroll", o, !0), window.addEventListener("resize", o);
}
var x = /* @__PURE__ */ new Map();
function S(e) {
	let t = ".managebar-menu,.board-local-nav:not(.settingscard>.board-local-nav)", n = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && n.push(e), n.forEach((e) => {
		if (e.hasAttribute("data-board-tabs")) return;
		e.dataset.boardTabs = "true";
		let t = e.className + e.getAttribute("aria-label"), n = (t) => {
			e.style.setProperty("--tab-x", `${t.left}px`), e.style.setProperty("--tab-width", `${t.width}px`);
		}, r = () => {
			let r = e.querySelector("button[aria-selected=true],button[aria-pressed=true]");
			if (!r || !r.offsetWidth) return;
			let i = {
				left: r.offsetLeft,
				width: r.offsetWidth
			};
			n(i), x.set(t, i);
		}, i = x.get(t);
		i ? n(i) : r(), requestAnimationFrame(() => {
			e.classList.add("board-tabs-ready"), requestAnimationFrame(r);
		});
		let a = new MutationObserver(r);
		a.observe(e, {
			subtree: !0,
			attributes: !0,
			attributeFilter: ["aria-selected", "aria-pressed"]
		});
		let o = new ResizeObserver(() => {
			if (!e.isConnected) {
				o.disconnect(), a.disconnect();
				return;
			}
			r();
		});
		o.observe(e);
	});
}
var C = /* @__PURE__ */ new Map();
function w(e) {
	let t = ".iconswitch,.insightswitch,.follow-workspace-switch", n = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && n.push(e), n.forEach((e) => {
		if (e.hasAttribute("data-board-segments") || e.closest("[data-skeleton]")) return;
		e.dataset.boardSegments = "true";
		let t = document.createElement("span");
		t.className = "board-segment-thumb", t.setAttribute("aria-hidden", "true"), e.prepend(t);
		let n = e.className + (e.getAttribute("aria-label") ?? ""), r = C.get(n) ?? null, a = () => {
			let a = e.querySelector("label:has(input:checked),button[aria-selected=true]");
			if (!a || !a.offsetWidth) return;
			let o = {
				x: a.offsetLeft,
				y: a.offsetTop,
				w: a.offsetWidth,
				h: a.offsetHeight
			};
			i(t, r, o, "x"), r = o, C.set(n, o);
		};
		e.addEventListener("change", a);
		let o = new MutationObserver(a);
		o.observe(e, {
			subtree: !0,
			attributes: !0,
			attributeFilter: ["aria-selected"]
		});
		let s = new ResizeObserver(() => {
			if (!e.isConnected) {
				s.disconnect(), o.disconnect();
				return;
			}
			a();
		});
		s.observe(e), a(), requestAnimationFrame(() => e.classList.add("board-segments-ready"));
	});
}
//#endregion
//#region src/sidebar-groups.ts
var T = (e) => e.replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function E(e, t, n = "", r = "") {
	if (!t) return "";
	let i = `sidebar-group-${encodeURIComponent(e)}`;
	return `<details class="sec${r ? " cat-" + T(r) : ""}" data-sidebar-group="${T(e)}"><summary role="button" class="board-section-toggle"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${T(e)}</span></summary><div class="board-sidebar-body" id="${i}">${t}${n}</div></details>`;
}
function D(e) {
	e.querySelectorAll("[data-sidebar-group]").forEach((e) => {
		if (e.dataset.sidebarWired) return;
		e.dataset.sidebarWired = "true";
		let t = e.querySelector(".board-sidebar-body"), n = `peach.sidebar.group.${e.dataset.sidebarGroup}`, r = null;
		try {
			r = sessionStorage.getItem(n);
		} catch {}
		let i = !!t.querySelector("[aria-pressed=true]");
		e.open = r === null ? i : r === "open";
	}), l(e, "details[data-sidebar-group]", "sidebar-collapse"), e.querySelectorAll(".board-section-toggle").forEach((e) => {
		e.dataset.persistWired || (e.dataset.persistWired = "true", e.addEventListener("click", () => {
			let t = `peach.sidebar.group.${e.closest("[data-sidebar-group]").dataset.sidebarGroup}`;
			try {
				sessionStorage.setItem(t, e.getAttribute("aria-expanded") === "true" ? "open" : "closed");
			} catch {}
		}));
	});
}
var O = !1;
async function k(e, t) {
	if (O) return;
	if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
		t();
		return;
	}
	let n = e.getBoundingClientRect(), r = n.left + n.width / 2, i = n.top + n.height / 2, a = Math.hypot(Math.max(r, innerWidth - r), Math.max(i, innerHeight - i)) * 2.5, o = document.createElement("style");
	o.textContent = `::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:radial-gradient(circle closest-side,#000 78%,#0006 88%,transparent);mask-repeat:no-repeat;will-change:mask-position,mask-size;animation:peach-theme-reveal 560ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${r}px ${i}px;mask-size:0px 0px}to{mask-position:${r - a / 2}px ${i - a / 2}px;mask-size:${a}px ${a}px}}`, O = !0, document.head.append(o);
	let s = document.documentElement;
	s.dataset.themeSnapshot = "true";
	let c = !1, l = () => {
		c || (c = !0, t());
	};
	try {
		await document.startViewTransition(l).finished;
	} catch {
		l();
	} finally {
		delete s.dataset.themeSnapshot, o.remove(), O = !1;
	}
}
//#endregion
//#region src/jobs.ts
function A(e, t, n) {
	if (!Number.isFinite(n) || n <= 0) return "";
	let r = Math.max(0, Math.min(n, Number.isFinite(t) ? t : 0)), i = r / n * 100;
	return `<div class="board-job-progress" role="progressbar" aria-label="${d(e)}" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${r}"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle class="board-job-track" cx="18" cy="18" r="15"/><circle class="board-job-fill" cx="18" cy="18" r="15" pathLength="100" stroke-dasharray="${i} ${100 - i}" transform="rotate(-90 18 18)"/></svg><span>${d(e)}<small>${Math.round(i)}%</small></span></div>`;
}
function j(e, t = 0, n = 0) {
	return n > 0 ? A(e, t, n) : r(e);
}
async function M(e) {
	let t = e.pause || ((e) => new Promise((t) => setTimeout(t, e))), n = 0;
	for (; e.active();) {
		let r;
		try {
			r = await e.read(AbortSignal.timeout(15e3));
		} catch (r) {
			if (!e.active()) return;
			n++, e.disconnected(r), await t(Math.min(2e3 * 2 ** Math.min(n, 4), 3e4));
			continue;
		}
		if (!e.active() || (n = 0, e.render(r), e.once) || !e.keepWatching && r.status !== "running") return;
		await t(2e3);
	}
}
function N(e) {
	let t = e.note || ((e) => a(e, {
		label: "任务状态",
		variant: "error"
	})), n = e.loading || r, i = e.progress || ((e, t, n) => j(n || `已处理 ${e} / ${t}`, e, t)), o = e.container || ((e) => `<section class="followtask" data-geist-fieldset aria-label="任务进度"><div class="geist-fieldset-content">${e}</div></section>`), s = document.createElement("div");
	e.host.hidden = !0, s.dataset.followJob = "", s.setAttribute("aria-live", "polite"), e.host.prepend(s);
	let c = e.storageKey || "peach-follow-job", l = sessionStorage.getItem(c) || void 0, u = !1;
	M({
		read: e.read,
		active: () => !u && e.active() && s.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (r) => {
			let a = r.status === "running";
			if (e.host.hidden = !a, e.busy(a), a) {
				l = r.job_id, l && sessionStorage.setItem(c, l);
				let t = r.current, a = (t?.attempt || 1) > 1 ? ` · 第 ${t?.attempt}/${t?.max_attempts} 次尝试${t?.retry_in ? `，${t.retry_in} 秒后重试` : ""}` : "", u = (r.message || (e.title ? e.title + (r.total ? `：已完成 ${r.checked || 0}/${r.total}` : "") : "") || (r.total ? `${r.older ? "抓取历史" : "检查更新"}：已完成 ${r.checked || 0}/${r.total} 个来源` : "正在准备检查任务…")) + (t ? ` · ${t.label || t.provider || ""}${a}` : ""), d = (r.total || 0) > 0 ? i(r.checked || 0, r.total, u) : n(u);
				s.innerHTML = o(d);
			} else if (l && l === r.job_id) l = void 0, u = !0, e.host.hidden = r.status !== "failed", sessionStorage.removeItem(c), s.innerHTML = r.status === "failed" ? t(r.error || "检查失败") : "", e.complete(r);
			else {
				if (l && r.status === "idle") {
					e.host.hidden = !1, s.innerHTML = t("任务状态已失效，请重新发起任务"), sessionStorage.removeItem(c), u = !0;
					return;
				}
				s.innerHTML = "";
			}
		},
		disconnected: () => {
			e.host.hidden = !1, s.innerHTML = t("暂时无法读取进度，正在重新连接…");
		}
	});
}
//#endregion
//#region src/review-evidence.ts
var P = (e = "") => /^https?:\/\//i.test(e) ? e : "";
function F(e = "") {
	let t = P(e) || (e.startsWith("/") && !e.startsWith("//") ? e : "");
	return `<div class="reviewimage" data-review-picture><span class="reviewimageempty"${t ? " hidden" : ""}>未取得来源图片</span>${t ? `<img src="${d(t)}" alt="来源候选图片" loading="lazy">` : ""}</div>`;
}
function I(e) {
	let t = P(e.profile_url), n = (e.preview_assets || []).slice(0, 6), r = Math.max(0, Number(e.video_count || e.videos || 0));
	return `<section class="reviewidentityevidence"><h5>候选身份：${d(e.babepedia_name || "未标注")}</h5>
    <div class="reviewevidenceactions">${t ? `<a class="geist-button externallink" href="${d(t)}" target="_blank" rel="noopener noreferrer">来源资料<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a>` : ""}
    <button type="button" class="geist-button" data-entity-kind="creator" data-entity-name="${d(e.creator || "")}">查看全部 ${r.toLocaleString()} 部作品</button></div>
    ${F(e.preview_url)}
    <p>通过后记录身份判断。</p>
    ${n.length ? `<h5>本地作品样本</h5><div class="reviewevidencesamples">${n.map((e) => `<div class="reviewevidencesample">
      <button class="geist-button" type="button" data-review-open-item="${e.id}"><span data-middle-truncate title="${d(e.name)}">${d(e.name)}</span></button>
      <button class="geist-button" type="button" data-review-reveal="${e.id}" aria-label="打开 ${d(e.name)} 的文件位置">文件位置</button>
    </div>`).join("")}</div>` : "<p>暂无本地作品样本，打开全部作品核对。</p>"}</section>`;
}
function L(e) {
	for (let t of e.querySelectorAll("[data-review-picture] img")) {
		let e = () => {
			t.hidden = !0;
			let e = t.parentElement?.querySelector(".reviewimageempty");
			e && (e.hidden = !1);
		};
		t.addEventListener("error", e), t.complete && !t.naturalWidth && e();
	}
}
//#endregion
//#region src/api.ts
var R = (e) => p(e);
//#endregion
//#region src/selection.ts
function z(e, t, n, r, i, a = i || !e.has(r)) {
	let o = n === null ? -1 : t.indexOf(n), s = t.indexOf(r);
	return i && o >= 0 && s >= 0 ? t.slice(Math.min(o, s), Math.max(o, s) + 1).forEach((t) => e.add(t)) : a ? e.add(r) : e.delete(r), r;
}
function ee(e, t) {
	let n = t.filter((t) => e.has(t)).length;
	return {
		count: n,
		all: n > 0 && n === t.length,
		mixed: n > 0 && n < t.length
	};
}
function te(e, t, n) {
	t.forEach((t) => n ? e.add(t) : e.delete(t));
}
function ne({ count: e, label: t, all: n, summary: r, actions: i, locked: a = !1 }) {
	e && (e.textContent = t), n && (n.checked = r.all, n.indeterminate = r.mixed);
	for (let e of i) e.disabled = !r.count || a;
}
//#endregion
//#region src/review-bulk.ts
var re = () => ({
	busy: !1,
	category: "",
	filter: "",
	groupBy: "candidates",
	anchor: null,
	selected: /* @__PURE__ */ new Set(),
	choices: /* @__PURE__ */ new Map(),
	assets: /* @__PURE__ */ new Map(),
	errors: /* @__PURE__ */ new Map()
});
function B(e) {
	let t = e?.querySelector(".reviewbulktoolbar");
	if (!e || e.classList.contains("review-skeleton") || !t || t.offsetParent === null) return;
	e.style.setProperty("--review-controls-height", `${t.getBoundingClientRect().height}px`);
	let n = [t, ...e.querySelectorAll(".reviewgroupbar")];
	for (let e of n) {
		let t = parseFloat(getComputedStyle(e).top);
		e.classList.toggle("is-stuck", e.offsetParent !== null && window.scrollY > 0 && Number.isFinite(t) && Math.abs(e.getBoundingClientRect().top - t) <= 1);
	}
	let r = n.filter((e) => e.classList.contains("is-stuck"));
	e.classList.toggle("review-is-stuck", r.length > 0);
	let i = t, a = n.slice(1).find((e) => e.offsetParent !== null && Math.abs(e.getBoundingClientRect().top - t.getBoundingClientRect().bottom) <= 2) || t;
	e.classList.add("review-has-pane"), n.forEach((e) => e.classList.toggle("review-pane-member", e === i || e === a));
	let o = i.getBoundingClientRect(), s = a.getBoundingClientRect();
	e.style.setProperty("--review-pane-top", `${o.top}px`), e.style.setProperty("--review-pane-left", `${o.left}px`), e.style.setProperty("--review-pane-width", `${o.width}px`), e.style.setProperty("--review-pane-height", `${s.bottom - o.top}px`);
}
function ie(e, t) {
	let n = [[
		"candidates",
		t ? "按候选数量" : "全部待复核",
		"list-filter"
	]];
	return e.some((e) => e.source || e.candidates?.some((e) => e.source)) && n.push([
		"source",
		"按来源",
		"list-filter"
	]), e.some((e) => e.field) && n.push([
		"field",
		"按字段",
		"list-filter"
	]), n;
}
function V(e, t) {
	let n = /* @__PURE__ */ new Map();
	for (let r of e) {
		let e, i;
		if (t === "field") e = r.field || "__unspecified_field", i = r.field_label || r.field || "未标注字段";
		else if (t === "source") {
			let t = [...new Set((r.candidates?.map((e) => e.source || "") || [r.source || ""]).filter(Boolean))].sort();
			e = JSON.stringify(t), i = t.join(" / ") || "未标注来源";
		} else e = r.candidates ? r.candidates.length === 1 ? "single" : "multiple" : "pending", i = e === "single" ? "单一候选" : e === "multiple" ? "需选择来源" : "待复核";
		n.has(e) || n.set(e, {
			key: e,
			title: i,
			rows: []
		}), n.get(e).rows.push(r);
	}
	return [...n.values()];
}
function H(e, t, n, r, i) {
	e.anchor = z(e.selected, t, e.anchor, n, r, i);
}
async function ae(e, t, n, r) {
	let i = [], a = 0;
	for (let o of e) {
		if (!r()) break;
		try {
			let e = await t(o.payload);
			if (!e.ok) throw Error(e.error || "服务端未采用该项");
			a++, n(o.key);
		} catch (e) {
			i.push({
				key: o.key,
				message: R(e)
			});
		}
	}
	return {
		completed: a,
		failures: i
	};
}
function U(e) {
	return e.length ? [...new Set(e.flatMap((e) => e.candidates?.map((e) => e.source || "") || []))].filter((t) => t && e.every((e) => e.candidates?.filter((e) => e.source === t).length === 1)) : [];
}
function oe(e, n) {
	let r = e.querySelector(".reviewlist");
	if (!r || !n.rows.length || n.locked) return;
	let i = n.state, a = [...r.querySelectorAll("[data-review-key]")];
	n.category !== void 0 && i.category !== n.category && (i.category = n.category, i.filter = "", i.groupBy = "candidates", i.anchor = null);
	let s = n.catalog || n.rows, l = ie(s, n.metadata);
	l.some((e) => e[0] === i.groupBy) || (i.groupBy = "candidates", i.filter = "");
	let d = V(s, i.groupBy);
	d.some((e) => e.key === i.filter) || (i.filter = "");
	let p = () => [...r.querySelectorAll("[data-review-key]")].filter((e) => !e.closest("[hidden]")), m = () => p().filter((e) => i.selected.has(e.dataset.reviewKey)), h = () => n.rows.filter((e) => m().some((t) => t.dataset.reviewKey === e.item_key)), g = (e) => !e.querySelector("[data-review-status=\"approved\"]")?.disabled, _ = (e, t = "") => {
		let n = document.createElement("button");
		return n.type = "button", n.className = `geist-button ${t}`.trim(), n.textContent = e, n;
	}, v = document.createElement("div");
	v.className = "reviewbulkbar reviewbulktoolbar", v.setAttribute("role", "group"), v.setAttribute("aria-label", "复核批量操作");
	let y = document.createElement("div");
	y.className = "reviewgroupby", y.innerHTML = o(l, i.groupBy, { label: "筛选分组方式" });
	let b = u(y.firstElementChild);
	y.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), b.addEventListener("change", () => {
		if (i.busy || !l.some((e) => e[0] === b.value)) return;
		i.groupBy = b.value, i.filter = "", i.anchor = null;
		let t = e.parentElement;
		n.refresh(), t?.querySelector(".reviewgroupby button")?.focus({ preventScroll: !0 });
	});
	let x = document.createElement("div");
	x.className = "reviewcategoryfilter", x.hidden = d.length < 2, x.innerHTML = o([[
		"",
		"全部分类",
		"list-filter"
	], ...d.map((e) => [
		e.key,
		`${e.title} · ${e.rows.length}`,
		"list-filter"
	])], i.filter, { label: i.groupBy === "field" ? "筛选字段分类" : "筛选当前分类" });
	let S = x.querySelector("[data-select-menu]");
	if (S) {
		let e = document.createElement("div");
		e.setAttribute("role", "group"), e.setAttribute("aria-label", i.groupBy === "field" ? "字段分类" : "当前分类");
		let t = document.createElement("div");
		t.className = "reviewfilterheading", t.textContent = e.getAttribute("aria-label"), t.setAttribute("aria-hidden", "true"), e.append(t, ...Array.from(S.children).slice(1)), S.append(e);
	}
	let C = u(x.firstElementChild);
	x.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), C.addEventListener("change", () => {
		if (i.busy || C.value && !d.some((e) => e.key === C.value)) return;
		i.filter = C.value, i.anchor = null;
		let t = e.parentElement;
		n.refresh(), t?.querySelector(".reviewcategoryfilter button")?.focus({ preventScroll: !0 });
	});
	let w = _("全选本页"), T = _("通过所选", "primary"), E = _("拒绝所选", "error"), D = document.createElement("span");
	D.className = "reviewselectedcount selectiondockcount", D.setAttribute("role", "status");
	let O = document.createElement("div");
	O.className = "reviewbulksource", O.hidden = !n.metadata;
	let k = document.createElement("p");
	k.className = "reviewstate reviewbulkfeedback", k.setAttribute("role", "status");
	let A = document.createElement("div");
	A.className = "reviewbulkdecisions", A.append(T, E);
	let j = document.createElement("div");
	j.className = "selectiondock reviewdock", j.setAttribute("role", "group"), j.setAttribute("aria-label", "复核所选项目");
	let M = _("取消选择");
	j.append(D, O, A, M, k), v.append(y, x, w);
	let N = e.querySelector(".reviewcontrols");
	N ? N.after(v) : r.before(v), e.append(j), r.classList.add("reviewgroups");
	let P = () => {
		i.selected.clear(), i.anchor = null, L();
	};
	M.onclick = () => {
		i.busy || (P(), w.focus({ preventScroll: !0 }));
	}, w.onclick = () => {
		if (i.busy) return;
		let e = p(), t = m().length === e.length;
		e.forEach((e) => t ? i.selected.delete(e.dataset.reviewKey) : i.selected.add(e.dataset.reviewKey)), L();
	}, T.onclick = () => R("approved", T), E.onclick = () => R("rejected", E);
	let F = [];
	for (let e of d) {
		let n = e.rows.map((e) => a.find((t) => t.dataset.reviewKey === e.item_key)).filter((e) => !!e);
		if (!n.length) continue;
		let o = document.createElement("section");
		o.className = "reviewgroup", o.hidden = !!i.filter && e.key !== i.filter;
		let s = document.createElement("div");
		s.className = "reviewbulkbar reviewgroupbar";
		let c = document.createElement("h3");
		c.textContent = `${e.title} · ${n.length}`;
		let l = _("全选本组"), u = document.createElement("div");
		u.className = "reviewlist", s.append(c, l), o.append(s, u), r.append(o), l.onclick = () => {
			if (i.busy) return;
			let e = n.map((e) => e.dataset.reviewKey);
			te(i.selected, e, !e.every((e) => i.selected.has(e))), L();
		}, F.push(() => {
			let e = n.every((e) => i.selected.has(e.dataset.reviewKey));
			l.innerHTML = f(e ? "check-check-outline" : "check-check") + (e ? "清空本组" : "全选本组"), l.setAttribute("aria-pressed", String(e));
		});
		for (let e of n) {
			u.append(e);
			let n = e.dataset.reviewKey;
			i.errors.has(n) && (e.querySelector(".reviewstate").textContent = i.errors.get(n));
			let r = e.querySelector("h4,.reviewentity b") || e, a = document.createElement("label");
			a.className = "reviewpickitem", a.innerHTML = t();
			let o = a.querySelector("input");
			if (o.setAttribute("aria-label", `选择 ${e.querySelector("legend")?.textContent || r.textContent || n}`), r !== e) {
				let e = document.createElement("span");
				e.className = "reviewpickname", e.append(...r.childNodes), r.classList.add("reviewpickheading"), r.append(a, e);
			} else e.prepend(a);
			let s = (e, t) => {
				H(i, p().map((e) => e.dataset.reviewKey), n, e, t), L();
			};
			if (a.addEventListener("mousedown", (e) => {
				e.shiftKey && e.preventDefault();
			}), a.addEventListener("click", (e) => {
				e.target !== o && (e.preventDefault(), i.busy || (o.focus(), s(e.shiftKey, !o.checked)));
			}), o.addEventListener("click", (e) => {
				i.busy || s(e.shiftKey, o.checked);
			}), o.addEventListener("keydown", (t) => {
				if (!(i.busy || !t.shiftKey)) {
					if (t.key === " ") t.preventDefault(), s(!0, !0);
					else if (t.key === "ArrowDown" || t.key === "ArrowUp") {
						t.preventDefault();
						let r = p(), a = r[r.indexOf(e) + (t.key === "ArrowDown" ? 1 : -1)];
						a && (i.anchor === null && (i.anchor = n), H(i, r.map((e) => e.dataset.reviewKey), a.dataset.reviewKey, !0, !0), L(), a.querySelector(".reviewpickitem input")?.focus());
					}
				}
			}), F.push(() => {
				o.checked = i.selected.has(n);
			}), i.assets.has(n)) {
				let t = i.assets.get(n), r = [...e.querySelectorAll("[data-review-asset]")];
				r.forEach((e) => {
					let n = t.includes(Number(e.dataset.reviewAsset));
					e.setAttribute("aria-pressed", String(n)), e.classList.toggle("picked", n);
				});
				let a = e.querySelector("[data-picked-count]");
				a && (a.textContent = `已选 ${t.length} / ${r.length}`);
			}
			e.addEventListener("click", (t) => {
				t.target.closest("[data-review-asset],[data-pick-all],[data-pick-none]") && i.assets.set(n, [...e.querySelectorAll("[data-review-asset][aria-pressed=\"true\"]")].map((e) => Number(e.dataset.reviewAsset)));
			});
			for (let t of e.querySelectorAll("input[type=\"radio\"]")) i.choices.has(n) && (t.checked = i.choices.get(n) === t.value), t.addEventListener("change", () => {
				t.checked && i.choices.set(n, t.value), L();
			});
		}
	}
	e.addEventListener("keydown", (t) => {
		i.busy || !e.contains(r) || (t.key === "Escape" && i.selected.size && (t.preventDefault(), t.stopPropagation(), P()), (t.ctrlKey || t.metaKey) && t.key.toLowerCase() === "a" && !t.target.matches("textarea,input:not([type=\"checkbox\"]):not([type=\"radio\"])") && (t.preventDefault(), t.stopPropagation(), p().forEach((e) => i.selected.add(e.dataset.reviewKey)), L()));
	});
	let I = "";
	function L() {
		let e = m(), t = e.length > 0 && e.length === p().length;
		w.innerHTML = f(t ? "check-check-outline" : "check-check") + (t ? "清空当前选择" : i.filter ? "全选当前分类" : "全选本页"), w.setAttribute("aria-pressed", String(t)), j.hidden = !e.length, ne({
			count: D,
			label: `已选 ${e.length} 项`,
			summary: ee(i.selected, p().map((e) => e.dataset.reviewKey)),
			actions: [T, E]
		}), T.disabled ||= e.some((e) => !g(e));
		let r = U(h());
		O.hidden = !n.metadata || !h().some((e) => (e.candidates?.length || 0) > 1);
		let a = e.length && !r.length ? "所选项目无共同来源" : "统一选择来源", s = JSON.stringify([a, r]);
		if (s !== I) {
			I = s, O.innerHTML = o([["", a], ...r.map((e) => [e, e])], "", { label: "统一选择来源" });
			let e = u(O.firstElementChild);
			e.disabled = !r.length, e.addEventListener("change", () => {
				if (!(i.busy || !U(h()).includes(e.value))) {
					for (let t of m()) {
						let r = n.rows.find((e) => e.item_key === t.dataset.reviewKey).candidates.find((t) => t.source === e.value);
						t.querySelectorAll("input[type=\"radio\"]").forEach((e) => {
							e.checked = e.value === r.candidate_key;
						}), i.choices.set(t.dataset.reviewKey, r.candidate_key);
					}
					k.textContent = `已选择 ${e.value}，点击通过所选采用。`;
				}
			});
		}
		F.forEach((e) => e());
	}
	async function R(t, r) {
		if (i.busy || !m().length) return;
		let a = m().map((e) => ({
			key: e.dataset.reviewKey,
			payload: {
				...n.payload(e),
				status: t
			}
		}));
		if (t === "approved" && n.metadata && a.some((e) => !e.payload.candidate_key)) {
			k.textContent = "请先为所选的多来源候选选择来源。", m().find((e) => !e.querySelector("input[type=\"radio\"]:checked"))?.querySelector("input[type=\"radio\"]")?.focus();
			return;
		}
		i.busy = !0, k.textContent = `正在处理 0 / ${a.length}`, c(r, !0);
		let o = [...e.querySelectorAll("button,input")], s = o.map((e) => e.getAttribute("aria-disabled"));
		o.forEach((e) => e.setAttribute("aria-disabled", "true"));
		let l = (e) => {
			e instanceof KeyboardEvent && e.key === "Tab" || (e.preventDefault(), e.stopImmediatePropagation());
		};
		e.addEventListener("click", l, !0), e.addEventListener("keydown", l, !0);
		let u = 0, d = await ae(a, async (e) => {
			try {
				return await n.submit(e);
			} finally {
				u++, n.active() && (k.textContent = `正在处理 ${u} / ${a.length}`);
			}
		}, (e) => {
			i.selected.delete(e), i.errors.delete(e), n.applied(e);
		}, n.active);
		if (i.busy = !1, e.removeEventListener("click", l, !0), e.removeEventListener("keydown", l, !0), o.forEach((e, t) => {
			let n = s[t];
			n === null ? e.removeAttribute("aria-disabled") : e.setAttribute("aria-disabled", n);
		}), c(r, !1), !n.active()) return;
		n.notify(`已${t === "approved" ? "通过" : "拒绝"} ${d.completed} 项${d.failures.length ? `，${d.failures.length} 项未完成` : ""}`), d.failures.forEach((e) => i.errors.set(e.key, e.message));
		let f = e.parentElement;
		n.refresh(), f?.querySelector(".reviewbulktoolbar button")?.focus({ preventScroll: !0 });
	}
	L(), B(e);
}
function se(e, t, n = 1) {
	let r = (e, t) => Array.from({ length: t - e + 1 }, (t, n) => e + n);
	if (n * 2 + 5 >= t) return r(1, t);
	let i = Math.max(e - n, 1), a = Math.min(e + n, t), o = i > 2, s = a < t - 2;
	return !o && s ? [
		...r(1, 3 + 2 * n),
		"…",
		t
	] : o && !s ? [
		1,
		"…",
		...r(t - (2 + 2 * n), t)
	] : [
		1,
		"…",
		...r(i, a),
		"…",
		t
	];
}
function ce(e, t) {
	return Math.max(1, Math.ceil(e / t));
}
function le(e, t) {
	return Math.min(Math.max(1, Math.floor(e) || 1), t);
}
function ue(e, t, n) {
	if (t <= 1) return "";
	let r = se(e, t).map((t) => t === "…" ? "<li class=\"board-page-dots\" aria-hidden=\"true\">…</li>" : `<li><button type="button" class="board-page" data-page="${t}" aria-label="第 ${t} 页"${t === e ? " aria-current=\"page\"" : ""}>${t}</button></li>`).join("");
	return `<nav class="board-pagination" aria-label="${n}">
    <button type="button" class="geist-button" data-page="${e - 1}"${e <= 1 ? " disabled" : ""}><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-left"></use></svg>上一页</button>
    <ul>${r}</ul>
    <button type="button" class="geist-button" data-page="${e + 1}"${e >= t ? " disabled" : ""}>下一页<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"></use></svg></button>
  </nav>`;
}
//#endregion
//#region src/native-image.ts
function de(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function fe(e, t, n, r, i = 1) {
	let a = Number.isFinite(i) && i > 0 ? i : 1;
	e /= a, t /= a;
	let o = [
		e,
		t,
		n,
		r
	].every((e) => Number.isFinite(e) && e > 0), s = o && Math.min(n, r) >= 64 && (e < n * .4 || t < r * .4), c = o ? Math.min(1, n / e, r / t) : 1;
	return {
		small: s,
		width: e * c,
		height: t * c
	};
}
//#endregion
//#region src/entity-skeleton.ts
function pe(e, t, n) {
	return `<section data-skeleton="entity/${e}" role="status" aria-label="正在读取资料">
    <span class="sr-only">正在读取资料</span><div aria-hidden="true">
    <section class="entityhero"><div class="entityprofile"><div class="entityportrait ${e === "studio" || e === "agency" ? "square " : ""}skeleton"></div>
      <div class="entityidentity entityskeletontext"><div class="entitytitle"><h2 class="skeleton">&nbsp;</h2></div>
      <div class="alias"><span class="skeleton"></span></div>
      <div class="entitylinks"><span class="skeleton"></span></div></div></div></section>
    <div class="board-filter-frame" data-filter-frame>
      <section class="entitytagbar" data-filter-row="top"><div class="filterscroll" data-skeleton-tier="pill"></div></section>
      ${t}</div>
    <div class="entitysection">${n}</div></div></section>`;
}
//#endregion
//#region src/board-skeleton.ts
var W = (e = "60%") => `<span class="skeleton" style="width:${e}"></span>`, G = () => `${W("80%")}${W("48%")}`, K = (e, t) => e.repeat(t), q = (e, t = "metricstrip") => `<div class="${t}">${e.map((e) => `<div class="tastesummary"><span class="board-stat-label">${e}</span><b class="board-stat-value">${W("45%")}</b><small class="board-stat-footer">${W("60%")}</small></div>`).join("")}</div>`, me = (e, t = "skeleton-tabs") => `<div class="${t}">${e.map((e) => `<span>${e}</span>`).join("")}</div>`, J = (e, t) => `<div class="${t} skeleton-segments" data-board-segments="true">${e.map((e, t) => `<span${t === 0 ? " class=\"skeleton-segment-selected\"" : ""}>${e}</span>`).join("")}</div>`, Y = (e) => `<section class="insightpanel"><header>${e}</header><div class="insightpanelbody skeleton-lines">${K(G(), 3)}</div></section>`, he = (e) => `<button class="fbtn" type="button" disabled>${e}</button>`, ge = (e) => `<div class="fsechead" data-collapse-toolbar><h3>关注列表</h3><span class="fmeta">${W("100px")}</span><div class="followtoolbaractions"><button class="fbtn primary followcheckall" disabled>${f("refresh-cw")}<span data-collapse-label>检查全部</span></button><div class="iconswitch" data-board-segments="true"><label>${f("layout-grid")}</label><label>${f("table")}</label></div><span class="fmanagesort" data-collapse-field>${f("sort")}${o([["checked", "检查时间"]], "checked", {
	label: "关注列表排序",
	attr: "disabled"
})}</span><button class="fbtn fmanagedir" disabled>${f("arrow-down")}</button>${e ? "" : he(f("chevron-up") + "<span data-collapse-label>全部收起</span>")}</div></div>`, _e = () => `<div class="fsource frow"><span class="fchannelcheck">${W("18px")}</span><b>${W("85%")}</b><span class="fprovider">${W("54px")}</span><span class="fmeta fchecked">${W("40px")}</span><span class="fsourceactions"><span class="skeleton skeleton-icon"></span><span class="skeleton skeleton-icon"></span></span></div>`, ve = () => `<details class="fauthor" open><summary class="fauthorhead"><span class="favatar skeleton"></span><b>${W("90px")}</b><span class="skeleton skeleton-icon"></span><span class="fmeta">${W("40px")}</span><span class="board-author-actions"><button type="button" class="fbtn small" data-follow-author-select disabled>${f("check-check")}<span data-author-select-label>全选</span></button><span class="skeleton skeleton-icon"></span></span></summary><div class="fauthorsources">${K(_e(), 3)}</div></details>`;
function ye() {
	return `<div data-skeleton="detail" role="status" aria-label="正在读取作品详情"><div class="sgrid" aria-hidden="true"><div class="vwrap skeleton-detail-media skeleton"></div><aside class="side"><div class="sidecontent skeleton-lines">${W("85%")}${W("65%")}${K(G(), 4)}</div></aside></div></div>`;
}
function be(e, n = {}) {
	let r = "";
	if (e === "/stats") r = `<div class="insightpage statsdashboard"><header class="insighttoolbar">${W("38%")}</header>${q([
		"馆藏视频",
		"看过",
		"内容标签",
		"使用空间"
	])}${Y("馆藏视频")}${Y("内容标签")}</div>`;
	else if (e === "/taste") r = `<div class="tastepage"><header class="tastehead">${J(["浏览器记录", "Peach 内部"], "insightswitch")}${W("24%")}</header><div class="tastestate"></div>${q([
		"浏览记录",
		"口味维度",
		"浏览候选",
		"私有导出"
	], "tastesummaries")}<section class="tastehero"><div class="insightcopy"><span>浏览器画像</span><div class="skeleton skeleton-radar"></div></div><div class="tastebars skeleton-lines">${K(G(), 4)}</div></section>${Y("口味分析")}<div class="board-activity-charts">${Y("浏览活动")}${Y("时间分布")}</div>${Y("标签")}</div>`;
	else if (e === "/follow-manage") {
		let e = n.followLayout === "table", i = e ? `<div class="ftableframe"><div class="ftablewrap"><table class="ftable"><thead><tr>${[
			"选择",
			"创作者",
			"来源",
			"站点",
			"状态",
			"上次检查",
			"操作"
		].map((e) => `<th>${e === "选择" ? "<label>" + t("disabled aria-label=\"全选本页来源\"") + "</label>" : e}</th>`).join("")}</tr></thead><tbody>${K(`<tr>${[
			"20px",
			"90px",
			"120px",
			"60px",
			"40px",
			"100px",
			"60px"
		].map((e) => `<td>${W(e)}</td>`).join("")}</tr>`, 6)}</tbody></table></div></div>` : `<div class="board-follow-list">${K(ve(), 4)}</div>`;
		r = `<div class="follow followmanage"><div class="fmanageoverview">${[
			"关注创作者",
			"启用来源",
			"检查失败",
			"未看更新"
		].map((e) => `<div><span>${e}</span><b>${W()}</b></div>`).join("")}</div>${J([
			"关注列表",
			"添加关注",
			"来源和凭证"
		], "follow-workspace-switch")}<div class="fmain"><section class="fsec" data-follow-workspace-panel="list">${ge(e)}<div class="board-follow-selection"${e ? " hidden" : ""}><label>${t("disabled")}全选本页</label></div><div class="frows fsources" data-layout="${e ? "table" : "default"}">${i}<div class="followpagefooter"><div class="followpageinfo">${W("120px")}${W("100px")}</div></div></div></section></div></div>`;
	} else if (e === "/configuration") r = `<div class="configpage">${me([
		"通用",
		"媒体",
		"网络与访问",
		"更新与维护"
	])}<section class="configfieldset"><div class="geist-fieldset-content"><h3 class="geist-fieldset-title">开机自启</h3><div class="skeleton-lines">${K(`<div class="skeleton-setting">${W("35%")}<span class="skeleton skeleton-toggle"></span></div>`, 3)}</div></div><footer class="geist-fieldset-footer">${W("100px")}</footer></section></div>`;
	else if (e === "/activity") r = `<div class="activitypage">${[
		"正在进行",
		"被挡下的",
		"最近完成"
	].map((e) => `<section class="activitysection"><h3 class="geist-fieldset-title">${e}</h3><div class="activity-runs"><article class="cleanupfieldset activity-run"><div class="geist-fieldset-content skeleton-lines">${W("35%")}${G()}</div></article></div></section>`).join("")}</div>`;
	else if (e === "/duplicates") r = `<div class="review"><div class="collection-summary">${W("38%")}</div><div class="fsechead dupactions"><h3>批量保留</h3>${W("40%")}</div>${K(`<section class="dupgroup"><div class="duphead">${W("45%")}</div><div class="duplist">${K(`<div class="duprow"><span class="dupcover skeleton"></span><span class="dupmarks">${W()}</span><span class="dupname">${W("90%")}</span>${W()}${W()}${W()}<span class="duppath">${W("70%")}</span></div>`, 2)}</div></section>`, 2)}</div>`;
	else if (e === "/quality-goals") r = `<div class="quality-workspace"><div class="collection-summary"><strong>待升级</strong>${W("20%")}</div><div class="qualitylist">${K(`<article class="qualityitem"><span class="qualitycover skeleton"></span><div class="qualitybody skeleton-lines">${G()}</div><footer class="qualityactions">${W("80%")}</footer></article>`, 6)}</div></div>`;
	else if (e === "/playlists") r = `<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><div class="playlistcreate skeleton-lines"><span>新播放列表</span>${W("200px")}</div></header><div class="playlistcards">${K(`<article class="card playlistcard"><div class="mixstack"><div class="pic skeleton"></div></div><div class="mixmeta"><span class="mav skeleton"></span><div class="mixcopy skeleton-lines">${G()}</div></div></article>`, 6)}</div></section>`;
	else return "";
	return `<div class="board-page-skeleton" data-skeleton="board${e}" role="status" aria-label="正在读取页面"><div aria-hidden="true" inert>${r}</div></div>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var xe = [
	"loc",
	"creator",
	"performer",
	"studio",
	"series",
	"agency",
	"tag",
	"tag_match",
	"len",
	"dur_min",
	"dur_max",
	"orient",
	"region",
	"state",
	"jav",
	"thumb"
];
function Se() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function Ce(e, t) {
	let n = new URLSearchParams();
	for (let t of xe) e[t] && n.set(t, e[t]);
	let [r, i] = await Promise.all([t("/api/facets?" + n), t("/api/items?" + n + "&limit=5")]), a = [...new Set([
		...r.creators || [],
		...r.tagperformers || [],
		...r.tags || []
	].map((e) => String(e.k || "")).concat((i.items || []).map((e) => e.code || e.name || "")))].filter((e) => e.length > 1).slice(0, 10);
	return (await Promise.all(a.map(async (e) => {
		let r = new URLSearchParams(n);
		return r.set("q", e), r.set("limit", "1"), (await t("/api/items?" + r)).total > 0 ? e : "";
	}))).filter(Boolean);
}
function we({ kind: e = "catalog", filtered: t = !1, jav: r = !1, configurable: i = !1, online: a = !1 } = {}) {
	let o = i ? "<button class=\"geist-button primary\" data-empty-settings>添加内容</button>" : "", s = "<a class=\"geist-button" + (!i || a ? " primary" : "") + "\" href=\"/follow-manage?tab=add\">添加关注</a>";
	if (t || r) return n("search", r ? "还没有符合条件的 JAV 作品" : "没有符合条件的内容", r ? "已扫描但尚未补充发行资料的视频可在全部内容中查看。" : "清除筛选或搜索条件后查看全部内容。", { actions: "<a class=\"geist-button primary\" href=\"/?loc=&thumb=0\">查看全部内容</a>" });
	if (e !== "catalog") {
		let t = (a ? {
			tags: "标签",
			performers: "创作者"
		}[e] : "") || {
			tags: "标签",
			performers: "艺人",
			creators: "创作者",
			studios: "厂牌",
			agencies: "事务所",
			series: "系列"
		}[e] || "资料";
		return n(e === "tags" ? "tags" : "user-round", "还没有" + t, a ? "添加关注来源并获取内容后，这里会显示来源上的" + t + "。" : "添加内容并补充资料后，这里会显示对应信息。", { actions: a ? s : o + s });
	}
	return n("play", "还没有视频", "添加媒体文件夹或关注来源，开始建立你的馆藏。", { actions: o + s });
}
//#endregion
//#region src/sidebar.ts
function Te(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function Ee(e, t) {
	return e.dataset.surface?.split("?")[0] === t.split("?")[0] && e.querySelector(".dnav") ? (e.dataset.surface = t, !1) : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function De(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function Oe(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function ke(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function Ae() {
	let e = [
		["人工复核", "square-check-big"],
		["高清版", "sparkles"],
		["重复文件", "file-stack"],
		["垃圾文件", "file-archive"],
		["回收站", "trash"]
	], t = "<span class=\"skeleton cleanup-count-skeleton\" aria-hidden=\"true\"></span>";
	return `<div class="cleanuppage" data-skeleton="cleanup" aria-busy="true" aria-label="正在读取数据管理状态">
    <div class="cleanupstats">${e.map(([e, n]) => `
      <button type="button" class="board-plain-stat" disabled>
        <span class="board-plain-stat-head"><span class="board-stat-tile"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-${n}"></use></svg></span>${e}</span>
        <strong>${t}</strong><span class="cleanupmeta">${t}</span></button>`).join("")}</div>
    <div class="cleanupgrid">
      <section class="cleanupfieldset board-processing-skeleton" data-geist-fieldset aria-labelledby="cleanup-loading-scan">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-scan">扫描与采集</h3>
          <p>扫描媒体文件夹，导入已有资料，采集缺失信息。</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><a class="board-link-button" href="/scraping"><span>来源和凭证</span><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-arrow-up"></use></svg></a><div class="splitbutton board-button-group primary"><button type="button" class="splitmain geist-button primary" disabled><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-database"></use></svg>扫描并补全资料</button><button type="button" class="splittoggle geist-button primary" disabled aria-label="更多扫描与采集方式"><svg aria-hidden="true"><use href="#i-chevron-down"></use></svg></button></div></footer>
      </section>
      <section class="cleanupfieldset cleanupemptyfolders" data-geist-fieldset aria-labelledby="cleanup-loading-empty">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-empty">空文件夹</h3>
          <strong>${t}</strong><p class="cleanupmeta">${t}</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" disabled><svg aria-hidden="true"><use href="#i-scan-search"></use></svg><span>扫描空文件夹</span></button></footer>
      </section></div>
    <section class="resourcesync" aria-labelledby="cleanup-loading-links">
      <h2 id="cleanup-loading-links">链接管理</h2>
      <div class="resourcesyncbox" data-geist-fieldset>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">站外链接</h3>
          <div class="linksummary"><div class="linkstats">${[
		"链接总数",
		"官网/事务所",
		"社交账号",
		"作品资料站",
		"资料出处"
	].map((e) => `<div><span>${e}</span><b>${t}</b></div>`).join("")}</div></div></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" type="button" disabled>检查死链</button></div>
      </div></section>
    <section class="resourcesync" aria-labelledby="cleanup-loading-sync">
      <h2 id="cleanup-loading-sync">资源同步</h2>
      <div class="resourcesyncbox" data-geist-fieldset>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">文件与记录核对</h3>
          <p>${t}</p></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" type="button" disabled>检查文件</button></div>
      </div></section></div>`;
}
//#endregion
//#region src/resource-sync.ts
var X = (e = 0) => Number(e).toLocaleString(), je = {
	local: "本地磁盘",
	115: "115",
	pikpak: "PikPak"
}, Me = (t) => s(e[t] ?? "database"), Z = (e, t, n) => `<article class="board-plain-stat resourcestat">
    <span class="board-plain-stat-head">${e}</span>
    <strong>${t}</strong>
    <span class="cleanupmeta">${n}</span></article>`;
function Ne(e, t) {
	let n = e.cache || {
		files: 0,
		bytes: 0
	}, r = !!(e.missing || n.files);
	return `<div class="cleanupstats resourcestats">${(e.sources || []).map((e) => Z(`<span class="board-stat-tile resourcestat-tile">${Me(e.location)}</span>${je[e.location] || "媒体来源"}<span class="resourcestat-state ${e.online ? "online" : "offline"}">${e.online ? "可访问" : "离线，已跳过"}</span>`, e.online ? `${X(e.missing)} 项` : "—", [e.online ? `找不到文件 · 已检查 ${X(e.checked)} 项` : `馆藏中有 ${X(e.total)} 项`, e.unreadable ? `${X(e.unreadable)} 项读取失败，已跳过` : ""].filter(Boolean).join(" · "))).join("")}
    ${Z("待移入回收站", `${X(e.missing)} 项`, "")}
    ${Z("可清理的缓存", `${X(n.files)} 个`, n.files ? t(n.bytes) : "")}</div>
    ${r ? a(`将把找不到文件的 ${X(e.missing)} 项馆藏记录移入回收站，并清理 ${X(n.files)} 个闲置缓存。`, { label: "清理内容" }) : ""}
    <div class="resourceapplyrow geist-fieldset-footer" data-geist-fieldset-footer>${r ? "<button class=\"geist-button primary\" type=\"button\" id=\"resourceApply\">清理失效记录与缓存</button>" : "<p class=\"resourcesyncok\">已检查可访问的来源，没有待清理的记录或缓存。</p>"}</div>`;
}
//#endregion
//#region src/jav-artwork.ts
function Pe(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function Fe(e) {
	return {
		javLayout: Pe(e.javLayout),
		javImage: Q(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function Q(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function Ie(e, t) {
	return e.is_jav && e.code && e.has_cover && (Q(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function Le(e, t) {
	let n = Number(e?.px?.[0]), r = Number(e?.px?.[1]), i = Number(e?.x0);
	if (!(n > 0 && r > 0 && t > 0) || !Number.isFinite(i)) return null;
	let a = Math.min(1, Math.max(0, i / n)), o = n / r / t, s = (1 - a) * o;
	if (!(s > 0)) return null;
	let c = s <= 1 ? (1 - s) / 2 - a * o : 1 - o, l = (e) => Math.round(e * 1e4) / 100;
	return {
		clip: l(a),
		left: l(c)
	};
}
function Re(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (Q(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.classList.remove("panel"), e.removeAttribute("style"), e.closest(".pic")?.style.removeProperty("--cover-blur"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var ze = {
	"avatar-picker": { react: "avatar-picker" },
	"follow-manage": { react: "follow-manage" },
	"library-processing": { react: "library-processing" },
	scraping: { react: "scraping" },
	"quality-goals": { react: "quality-goals" },
	configuration: { react: "configuration" },
	activity: { react: "activity" },
	stats: { react: "stats" },
	taste: { react: "taste" }
}, Be = () => Object.keys(ze), $ = /* @__PURE__ */ new Map();
async function Ve(e, t, n, r = {}) {
	let i = ze[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	We(t);
	let a = { controller: new AbortController() };
	$.set(t, a);
	let o = (await import("/dist/peach-react.js")).pages[i.react];
	try {
		await o.prefetch(n, a.controller.signal);
	} catch {
		if (a.controller.signal.aborted) return;
	}
	if (!He(t, a, r)) return;
	let s = t.ownerDocument.createElement("div");
	s.className = "peach-react", t.append(s);
	let c = o.mount(s, n);
	a.dispose = () => {
		c.unmount(), s.remove();
	};
}
function He(e, t, n) {
	return $.get(e) === t ? n.isCurrent && !n.isCurrent() ? ($.delete(e), !1) : (e.textContent = "", !0) : !1;
}
var Ue = (e) => !!e && $.has(e);
function We(e) {
	for (let t of [...$.keys()]) (t === e || e.contains(t)) && Ge(t);
}
function Ge(e) {
	let t = $.get(e);
	t && (t.controller.abort(), $.delete(e), t.dispose?.());
}
//#endregion
export { be as boardPageSkeleton, g as boundedPreference, we as catalogEmptyHtml, Ce as catalogSuggestions, le as clampPage, Ae as cleanupSkeletonHtml, Oe as cloudLocations, ke as cloudPreferenceLocations, re as createReviewSelection, ye as detailSkeletonHtml, Se as emptyCatalogLayout, pe as entitySkeletonHtml, N as followJobProgress, V as groupReviewRows, I as identityEvidenceHtml, b as initBoardControls, Ue as islandMounted, Be as islandNames, Ie as javImageKind, j as jobActivityHtml, de as matchesFaceSource, Ve as mountIsland, v as mountNumberSetting, fe as nativeImageFit, Q as normalizeJavImage, Pe as normalizeJavLayout, Fe as normalizeJavPreferences, ce as pageCount, ue as paginationHtml, Le as panelFrame, m as preferredDirection, Ne as resourceScanHtml, F as reviewImageHtml, te as selectGroup, z as selectRange, ee as selectionSummary, Te as sidebarHasCatalogContent, E as sidebarSectionHtml, De as sidebarTagCounts, y as syncBoardRange, Re as syncJavImages, _ as syncNumberSetting, ne as syncSelectionToolbar, Ee as syncSidebarSurface, k as transitionTheme, We as unmountIsland, B as updateReviewSticky, M as watchJob, L as wireReviewPictures, oe as wireReviewSelection, D as wireSidebarGroups };
