import { MEDIA_SOURCE_ICONS as e, checkboxHtml as t, emptyStateHtml as n, loadingDotsHtml as r, moveGlidePane as i, noteHtml as a, selectFieldHtml as o, selectOptionIconHtml as s, wireCollapse as c } from "/js/ui-components.js";
import { esc as l, icon as u } from "/js/core.js";
//#region src/sort-preferences.ts
function d(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/number-setting.ts
var f = {
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
function p(e, t, n, r) {
	return Number.isInteger(e) && e >= t && e <= n ? e : r;
}
function m(e, t, n) {
	let r = e.querySelector("input[type=number]"), i = e.querySelector("[role=switch]"), a = e.querySelector(".board-number-fields");
	r && (r.disabled = n, t !== null && t > 0 && (r.value = String(t))), i && (i.disabled = n, t !== null && (i.checked = t > 0)), a && t !== null && (a.hidden = t === 0);
}
function h(e, t, n, r, i) {
	let a = f[t];
	if (!a) return !1;
	let { min: o, max: s, unit: c, optional: l, fallback: u } = a, d = `peach.number.${t}`, m = p(Number(localStorage.getItem(d)), o, s, r > 0 ? r : u), h = document.createElement("div");
	h.className = "board-optional-number";
	let g = document.createElement("div");
	g.className = "board-number-fields", g.hidden = !!l && r === 0;
	let _ = document.createElement("div");
	_.className = "board-number-control";
	let v = document.createElement("input");
	v.type = "number", v.className = "geist-input", v.min = String(o), v.max = String(s), v.step = "1", v.value = String(r > 0 ? r : m), v.setAttribute("aria-label", n);
	let y = document.createElement("span");
	y.textContent = c, y.setAttribute("aria-hidden", "true");
	let b = document.createElement("small");
	b.id = `${t}-error`, b.className = "board-number-error", b.setAttribute("role", "status"), b.hidden = !0, v.setAttribute("aria-describedby", b.id), _.append(v, y), g.append(_, b), h.append(g), e.replaceChildren(h);
	let x = () => {
		v.removeAttribute("aria-invalid"), b.hidden = !0, b.textContent = "";
	}, S = () => {
		if (!v.value || !v.checkValidity()) {
			v.setAttribute("aria-invalid", "true"), b.textContent = `请输入 ${o}–${s} 的整数（${c}）`, b.hidden = !1;
			return;
		}
		x(), m = Number(v.value), localStorage.setItem(d, String(m)), i(v.value);
	};
	if (v.addEventListener("change", S), v.addEventListener("keydown", (e) => {
		e.key === "Enter" && (e.preventDefault(), S());
	}), v.addEventListener("input", () => {
		v.value && v.checkValidity() && x();
	}), l) {
		let e = document.createElement("input");
		e.type = "checkbox", e.className = "ptoggle", e.setAttribute("role", "switch"), e.setAttribute("aria-label", `启用${n}`), e.checked = r > 0, e.onchange = () => {
			x(), g.hidden = !e.checked, e.checked ? (v.value = String(m), S()) : (v.value && v.checkValidity() && (m = Number(v.value)), localStorage.setItem(d, String(m)), i("0"));
		}, h.prepend(e);
	}
	return !0;
}
//#endregion
//#region src/board-controls.ts
function g(e) {
	let t = Number(e.min) || 0, n = Number(e.max) || 100, r = Number(e.value), i = n > t ? Math.max(0, Math.min(100, (r - t) / (n - t) * 100)) : 0;
	e.style.setProperty("--board-range-value", `${i}%`);
	let a = e.closest(".dual-range");
	if (!a) return;
	let o = e.id === "durMax" ? "max" : "min", s = a.querySelector(`[data-range-end="${o}"]`);
	s || (s = document.createElement("output"), s.className = "board-range-tip", s.dataset.rangeEnd = o, s.setAttribute("aria-hidden", "true"), a.append(s)), s.textContent = r >= n && o === "max" ? "不限" : `${r} 分钟`, s.style.left = `${i}%`, s.style.setProperty("--range-tip-shift", "0px");
	let c = a.getBoundingClientRect(), l = s.getBoundingClientRect(), u = l.right > c.right ? c.right - l.right : l.left < c.left ? c.left - l.left : 0;
	u && s.style.setProperty("--range-tip-shift", `${Math.round(u)}px`), a.querySelectorAll(".board-range-tip").forEach((e) => e.toggleAttribute("data-range-active", e === s));
}
function _() {
	let e = (e) => {
		e.querySelectorAll("input[type=range]").forEach(g), x(e), y(e);
	};
	e(document), new MutationObserver((t) => {
		for (let n of t) for (let t of n.addedNodes) t instanceof Element && (t.matches("input[type=range]") && g(t), e(t));
	}).observe(document.body, {
		subtree: !0,
		childList: !0
	}), document.addEventListener("input", (e) => {
		e.target instanceof HTMLInputElement && e.target.type === "range" && g(e.target);
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
var v = /* @__PURE__ */ new Map();
function y(e) {
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
			n(i), v.set(t, i);
		}, i = v.get(t);
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
var b = /* @__PURE__ */ new Map();
function x(e) {
	let t = ".iconswitch,.insightswitch,.follow-workspace-switch", n = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && n.push(e), n.forEach((e) => {
		if (e.hasAttribute("data-board-segments") || e.closest("[data-skeleton]")) return;
		e.dataset.boardSegments = "true";
		let t = document.createElement("span");
		t.className = "board-segment-thumb", t.setAttribute("aria-hidden", "true"), e.prepend(t);
		let n = e.className + (e.getAttribute("aria-label") ?? ""), r = b.get(n) ?? null, a = () => {
			let a = e.querySelector("label:has(input:checked),button[aria-selected=true]");
			if (!a || !a.offsetWidth) return;
			let o = {
				x: a.offsetLeft,
				y: a.offsetTop,
				w: a.offsetWidth,
				h: a.offsetHeight
			};
			i(t, r, o, "x"), r = o, b.set(n, o);
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
var S = (e) => e.replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function C(e, t, n = "", r = "") {
	if (!t) return "";
	let i = `sidebar-group-${encodeURIComponent(e)}`;
	return `<details class="sec${r ? " cat-" + S(r) : ""}" data-sidebar-group="${S(e)}"><summary role="button" class="board-section-toggle"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${S(e)}</span></summary><div class="board-sidebar-body" id="${i}">${t}${n}</div></details>`;
}
function w(e) {
	e.querySelectorAll("[data-sidebar-group]").forEach((e) => {
		if (e.dataset.sidebarWired) return;
		e.dataset.sidebarWired = "true";
		let t = e.querySelector(".board-sidebar-body"), n = `peach.sidebar.group.${e.dataset.sidebarGroup}`, r = null;
		try {
			r = sessionStorage.getItem(n);
		} catch {}
		let i = !!t.querySelector("[aria-pressed=true]");
		e.open = r === null ? i : r === "open";
	}), c(e, "details[data-sidebar-group]", "sidebar-collapse"), e.querySelectorAll(".board-section-toggle").forEach((e) => {
		e.dataset.persistWired || (e.dataset.persistWired = "true", e.addEventListener("click", () => {
			let t = `peach.sidebar.group.${e.closest("[data-sidebar-group]").dataset.sidebarGroup}`;
			try {
				sessionStorage.setItem(t, e.getAttribute("aria-expanded") === "true" ? "open" : "closed");
			} catch {}
		}));
	});
}
var T = !1;
async function E(e, t) {
	if (T) return;
	if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
		t();
		return;
	}
	let n = e.getBoundingClientRect(), r = n.left + n.width / 2, i = n.top + n.height / 2, a = Math.hypot(Math.max(r, innerWidth - r), Math.max(i, innerHeight - i)) * 2.5, o = document.createElement("style");
	o.textContent = `::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:radial-gradient(circle closest-side,#000 78%,#0006 88%,transparent);mask-repeat:no-repeat;will-change:mask-position,mask-size;animation:peach-theme-reveal 560ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${r}px ${i}px;mask-size:0px 0px}to{mask-position:${r - a / 2}px ${i - a / 2}px;mask-size:${a}px ${a}px}}`, T = !0, document.head.append(o);
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
		delete s.dataset.themeSnapshot, o.remove(), T = !1;
	}
}
//#endregion
//#region src/jobs.ts
function ee(e, t, n) {
	if (!Number.isFinite(n) || n <= 0) return "";
	let r = Math.max(0, Math.min(n, Number.isFinite(t) ? t : 0)), i = r / n * 100;
	return `<div class="board-job-progress" role="progressbar" aria-label="${l(e)}" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${r}"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle class="board-job-track" cx="18" cy="18" r="15"/><circle class="board-job-fill" cx="18" cy="18" r="15" pathLength="100" stroke-dasharray="${i} ${100 - i}" transform="rotate(-90 18 18)"/></svg><span>${l(e)}<small>${Math.round(i)}%</small></span></div>`;
}
function D(e, t = 0, n = 0) {
	return n > 0 ? ee(e, t, n) : r(e);
}
async function O(e) {
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
function te(e) {
	let t = e.note || ((e) => a(e, {
		label: "任务状态",
		variant: "error"
	})), n = e.loading || r, i = e.progress || ((e, t, n) => D(n || `已处理 ${e} / ${t}`, e, t)), o = e.container || ((e) => `<section class="followtask" data-geist-fieldset aria-label="任务进度"><div class="geist-fieldset-content">${e}</div></section>`), s = document.createElement("div");
	e.host.hidden = !0, s.dataset.followJob = "", s.setAttribute("aria-live", "polite"), e.host.prepend(s);
	let c = e.storageKey || "peach-follow-job", l = sessionStorage.getItem(c) || void 0, u = !1;
	O({
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
//#region src/selection.ts
function ne(e, t, n, r, i, a = i || !e.has(r)) {
	let o = n === null ? -1 : t.indexOf(n), s = t.indexOf(r);
	return i && o >= 0 && s >= 0 ? t.slice(Math.min(o, s), Math.max(o, s) + 1).forEach((t) => e.add(t)) : a ? e.add(r) : e.delete(r), r;
}
function re(e, t) {
	let n = t.filter((t) => e.has(t)).length;
	return {
		count: n,
		all: n > 0 && n === t.length,
		mixed: n > 0 && n < t.length
	};
}
function k(e, t, n) {
	t.forEach((t) => n ? e.add(t) : e.delete(t));
}
function A({ count: e, label: t, all: n, summary: r, actions: i, locked: a = !1 }) {
	e && (e.textContent = t), n && (n.checked = r.all, n.indeterminate = r.mixed);
	for (let e of i) e.disabled = !r.count || a;
}
function ie(e, t, n = 1) {
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
function ae(e, t) {
	return Math.max(1, Math.ceil(e / t));
}
function oe(e, t) {
	return Math.min(Math.max(1, Math.floor(e) || 1), t);
}
function se(e, t, n) {
	if (t <= 1) return "";
	let r = ie(e, t).map((t) => t === "…" ? "<li class=\"board-page-dots\" aria-hidden=\"true\">…</li>" : `<li><button type="button" class="board-page" data-page="${t}" aria-label="第 ${t} 页"${t === e ? " aria-current=\"page\"" : ""}>${t}</button></li>`).join("");
	return `<nav class="board-pagination" aria-label="${n}">
    <button type="button" class="geist-button" data-page="${e - 1}"${e <= 1 ? " disabled" : ""}><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-left"></use></svg>上一页</button>
    <ul>${r}</ul>
    <button type="button" class="geist-button" data-page="${e + 1}"${e >= t ? " disabled" : ""}>下一页<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"></use></svg></button>
  </nav>`;
}
//#endregion
//#region src/native-image.ts
function ce(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function j(e, t, n, r, i = 1) {
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
function M(e, t, n) {
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
var N = (e = "60%") => `<span class="skeleton" style="width:${e}"></span>`, P = () => `${N("80%")}${N("48%")}`, F = (e, t) => e.repeat(t), I = (e, t = "metricstrip") => `<div class="${t}">${e.map((e) => `<div class="tastesummary"><span class="board-stat-label">${e}</span><b class="board-stat-value">${N("45%")}</b><small class="board-stat-footer">${N("60%")}</small></div>`).join("")}</div>`, L = (e, t = "skeleton-tabs") => `<div class="${t}">${e.map((e) => `<span>${e}</span>`).join("")}</div>`, R = (e, t) => `<div class="${t} skeleton-segments" data-board-segments="true">${e.map((e, t) => `<span${t === 0 ? " class=\"skeleton-segment-selected\"" : ""}>${e}</span>`).join("")}</div>`, z = (e) => `<section class="insightpanel"><header>${e}</header><div class="insightpanelbody skeleton-lines">${F(P(), 3)}</div></section>`, B = (e) => `<button class="fbtn" type="button" disabled>${e}</button>`, V = (e) => `<div class="fsechead" data-collapse-toolbar><h3>关注列表</h3><span class="fmeta">${N("100px")}</span><div class="followtoolbaractions"><button class="fbtn primary followcheckall" disabled>${u("refresh-cw")}<span data-collapse-label>检查全部</span></button><div class="iconswitch" data-board-segments="true"><label>${u("layout-grid")}</label><label>${u("table")}</label></div><span class="fmanagesort" data-collapse-field>${u("sort")}${o([["checked", "检查时间"]], "checked", {
	label: "关注列表排序",
	attr: "disabled"
})}</span><button class="fbtn fmanagedir" disabled>${u("arrow-down")}</button>${e ? "" : B(u("chevron-up") + "<span data-collapse-label>全部收起</span>")}</div></div>`, H = () => `<div class="fsource frow"><span class="fchannelcheck">${N("18px")}</span><b>${N("85%")}</b><span class="fprovider">${N("54px")}</span><span class="fmeta fchecked">${N("40px")}</span><span class="fsourceactions"><span class="skeleton skeleton-icon"></span><span class="skeleton skeleton-icon"></span></span></div>`, U = () => `<details class="fauthor" open><summary class="fauthorhead"><span class="favatar skeleton"></span><b>${N("90px")}</b><span class="skeleton skeleton-icon"></span><span class="fmeta">${N("40px")}</span><span class="board-author-actions"><button type="button" class="fbtn small" data-follow-author-select disabled>${u("check-check")}<span data-author-select-label>全选</span></button><span class="skeleton skeleton-icon"></span></span></summary><div class="fauthorsources">${F(H(), 3)}</div></details>`;
function W() {
	return `<div data-skeleton="detail" role="status" aria-label="正在读取作品详情"><div class="sgrid" aria-hidden="true"><div class="vwrap skeleton-detail-media skeleton"></div><aside class="side"><div class="sidecontent skeleton-lines">${N("85%")}${N("65%")}${F(P(), 4)}</div></aside></div></div>`;
}
function G(e, n = {}) {
	let r = "";
	if (e === "/stats") r = `<div class="insightpage statsdashboard"><header class="insighttoolbar">${N("38%")}</header>${I([
		"馆藏视频",
		"看过",
		"内容标签",
		"使用空间"
	])}${z("馆藏视频")}${z("内容标签")}</div>`;
	else if (e === "/taste") r = `<div class="tastepage"><header class="tastehead">${R(["浏览器记录", "Peach 内部"], "insightswitch")}${N("24%")}</header><div class="tastestate"></div>${I([
		"浏览记录",
		"口味维度",
		"浏览候选",
		"私有导出"
	], "tastesummaries")}<section class="tastehero"><div class="insightcopy"><span>浏览器画像</span><div class="skeleton skeleton-radar"></div></div><div class="tastebars skeleton-lines">${F(P(), 4)}</div></section>${z("口味分析")}<div class="board-activity-charts">${z("浏览活动")}${z("时间分布")}</div>${z("标签")}</div>`;
	else if (e === "/follow-manage") {
		let e = n.followLayout === "table", i = e ? `<div class="ftableframe"><div class="ftablewrap"><table class="ftable"><thead><tr>${[
			"选择",
			"创作者",
			"来源",
			"站点",
			"状态",
			"上次检查",
			"操作"
		].map((e) => `<th>${e === "选择" ? "<label>" + t("disabled aria-label=\"全选本页来源\"") + "</label>" : e}</th>`).join("")}</tr></thead><tbody>${F(`<tr>${[
			"20px",
			"90px",
			"120px",
			"60px",
			"40px",
			"100px",
			"60px"
		].map((e) => `<td>${N(e)}</td>`).join("")}</tr>`, 6)}</tbody></table></div></div>` : `<div class="board-follow-list">${F(U(), 4)}</div>`;
		r = `<div class="follow followmanage"><div class="fmanageoverview">${[
			"关注创作者",
			"启用来源",
			"检查失败",
			"未看更新"
		].map((e) => `<div><span>${e}</span><b>${N()}</b></div>`).join("")}</div>${R([
			"关注列表",
			"添加关注",
			"来源和凭证"
		], "follow-workspace-switch")}<div class="fmain"><section class="fsec" data-follow-workspace-panel="list">${V(e)}<div class="board-follow-selection"${e ? " hidden" : ""}><label>${t("disabled")}全选本页</label></div><div class="frows fsources" data-layout="${e ? "table" : "default"}">${i}<div class="followpagefooter"><div class="followpageinfo">${N("120px")}${N("100px")}</div></div></div></section></div></div>`;
	} else if (e === "/configuration") r = `<div class="configpage">${L([
		"通用",
		"媒体",
		"网络与访问",
		"更新与维护"
	])}<section class="configfieldset"><div class="geist-fieldset-content"><h3 class="geist-fieldset-title">开机自启</h3><div class="skeleton-lines">${F(`<div class="skeleton-setting">${N("35%")}<span class="skeleton skeleton-toggle"></span></div>`, 3)}</div></div><footer class="geist-fieldset-footer">${N("100px")}</footer></section></div>`;
	else if (e === "/activity") r = `<div class="activitypage">${[
		"正在进行",
		"被挡下的",
		"最近完成"
	].map((e) => `<section class="activitysection"><h3 class="geist-fieldset-title">${e}</h3><div class="activity-runs"><article class="cleanupfieldset activity-run"><div class="geist-fieldset-content skeleton-lines">${N("35%")}${P()}</div></article></div></section>`).join("")}</div>`;
	else if (e === "/duplicates") r = `<div class="review"><div class="collection-summary">${N("38%")}</div><div class="fsechead dupactions"><h3>批量保留</h3>${N("40%")}</div>${F(`<section class="dupgroup"><div class="duphead">${N("45%")}</div><div class="duplist">${F(`<div class="duprow"><span class="dupcover skeleton"></span><span class="dupmarks">${N()}</span><span class="dupname">${N("90%")}</span>${N()}${N()}${N()}<span class="duppath">${N("70%")}</span></div>`, 2)}</div></section>`, 2)}</div>`;
	else if (e === "/quality-goals") r = `<div class="quality-workspace"><div class="collection-summary"><strong>待升级</strong>${N("20%")}</div><div class="qualitylist">${F(`<article class="qualityitem"><span class="qualitycover skeleton"></span><div class="qualitybody skeleton-lines">${P()}</div><footer class="qualityactions">${N("80%")}</footer></article>`, 6)}</div></div>`;
	else if (e === "/playlists") r = `<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><div class="playlistcreate skeleton-lines"><span>新播放列表</span>${N("200px")}</div></header><div class="playlistcards">${F(`<article class="card playlistcard"><div class="mixstack"><div class="pic skeleton"></div></div><div class="mixmeta"><span class="mav skeleton"></span><div class="mixcopy skeleton-lines">${P()}</div></div></article>`, 6)}</div></section>`;
	else return "";
	return `<div class="board-page-skeleton" data-skeleton="board${e}" role="status" aria-label="正在读取页面"><div aria-hidden="true" inert>${r}</div></div>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var K = [
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
function le() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function ue(e, t) {
	let n = new URLSearchParams();
	for (let t of K) e[t] && n.set(t, e[t]);
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
function de({ kind: e = "catalog", filtered: t = !1, jav: r = !1, configurable: i = !1, online: a = !1 } = {}) {
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
function fe(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function pe(e, t) {
	return e.dataset.surface?.split("?")[0] === t.split("?")[0] && e.querySelector(".dnav") ? (e.dataset.surface = t, !1) : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function me(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function he(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function ge(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function _e() {
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
var q = (e = 0) => Number(e).toLocaleString(), ve = {
	local: "本地磁盘",
	115: "115",
	pikpak: "PikPak"
}, ye = (t) => s(e[t] ?? "database"), J = (e, t, n) => `<article class="board-plain-stat resourcestat">
    <span class="board-plain-stat-head">${e}</span>
    <strong>${t}</strong>
    <span class="cleanupmeta">${n}</span></article>`;
function be(e, t) {
	let n = e.cache || {
		files: 0,
		bytes: 0
	}, r = !!(e.missing || n.files);
	return `<div class="cleanupstats resourcestats">${(e.sources || []).map((e) => J(`<span class="board-stat-tile resourcestat-tile">${ye(e.location)}</span>${ve[e.location] || "媒体来源"}<span class="resourcestat-state ${e.online ? "online" : "offline"}">${e.online ? "可访问" : "离线，已跳过"}</span>`, e.online ? `${q(e.missing)} 项` : "—", [e.online ? `找不到文件 · 已检查 ${q(e.checked)} 项` : `馆藏中有 ${q(e.total)} 项`, e.unreadable ? `${q(e.unreadable)} 项读取失败，已跳过` : ""].filter(Boolean).join(" · "))).join("")}
    ${J("待移入回收站", `${q(e.missing)} 项`, "")}
    ${J("可清理的缓存", `${q(n.files)} 个`, n.files ? t(n.bytes) : "")}</div>
    ${r ? a(`将把找不到文件的 ${q(e.missing)} 项馆藏记录移入回收站，并清理 ${q(n.files)} 个闲置缓存。`, { label: "清理内容" }) : ""}
    <div class="resourceapplyrow geist-fieldset-footer" data-geist-fieldset-footer>${r ? "<button class=\"geist-button primary\" type=\"button\" id=\"resourceApply\">清理失效记录与缓存</button>" : "<p class=\"resourcesyncok\">已检查可访问的来源，没有待清理的记录或缓存。</p>"}</div>`;
}
//#endregion
//#region src/jav-artwork.ts
function Y(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function xe(e) {
	return {
		javLayout: Y(e.javLayout),
		javImage: X(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function X(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function Se(e, t) {
	return e.is_jav && e.code && e.has_cover && (X(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function Ce(e, t) {
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
function we(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (X(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.classList.remove("panel"), e.removeAttribute("style"), e.closest(".pic")?.style.removeProperty("--cover-blur"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var Z = {
	"avatar-picker": { react: "avatar-picker" },
	"follow-manage": { react: "follow-manage" },
	"library-processing": { react: "library-processing" },
	scraping: { react: "scraping" },
	"quality-goals": { react: "quality-goals" },
	review: { react: "review" },
	configuration: { react: "configuration" },
	activity: { react: "activity" },
	stats: { react: "stats" },
	taste: { react: "taste" }
}, Te = () => Object.keys(Z), Q = /* @__PURE__ */ new Map();
async function Ee(e, t, n, r = {}) {
	let i = Z[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	$(t);
	let a = { controller: new AbortController() };
	Q.set(t, a);
	let o = (await import("/dist/peach-react.js")).pages[i.react];
	try {
		await o.prefetch(n, a.controller.signal);
	} catch {
		if (a.controller.signal.aborted) return;
	}
	if (!De(t, a, r)) return;
	let s = t.ownerDocument.createElement("div");
	s.className = "peach-react", t.append(s);
	let c = o.mount(s, n);
	a.dispose = () => {
		c.unmount(), s.remove();
	};
}
function De(e, t, n) {
	return Q.get(e) === t ? n.isCurrent && !n.isCurrent() ? (Q.delete(e), !1) : (e.textContent = "", !0) : !1;
}
var Oe = (e) => !!e && Q.has(e);
function $(e) {
	for (let t of [...Q.keys()]) (t === e || e.contains(t)) && ke(t);
}
function ke(e) {
	let t = Q.get(e);
	t && (t.controller.abort(), Q.delete(e), t.dispose?.());
}
//#endregion
export { G as boardPageSkeleton, p as boundedPreference, de as catalogEmptyHtml, ue as catalogSuggestions, oe as clampPage, _e as cleanupSkeletonHtml, he as cloudLocations, ge as cloudPreferenceLocations, W as detailSkeletonHtml, le as emptyCatalogLayout, M as entitySkeletonHtml, te as followJobProgress, _ as initBoardControls, Oe as islandMounted, Te as islandNames, Se as javImageKind, D as jobActivityHtml, ce as matchesFaceSource, Ee as mountIsland, h as mountNumberSetting, j as nativeImageFit, X as normalizeJavImage, Y as normalizeJavLayout, xe as normalizeJavPreferences, ae as pageCount, se as paginationHtml, Ce as panelFrame, d as preferredDirection, be as resourceScanHtml, k as selectGroup, ne as selectRange, re as selectionSummary, fe as sidebarHasCatalogContent, C as sidebarSectionHtml, me as sidebarTagCounts, g as syncBoardRange, we as syncJavImages, m as syncNumberSetting, A as syncSelectionToolbar, pe as syncSidebarSurface, E as transitionTheme, $ as unmountIsland, O as watchJob, w as wireSidebarGroups };
