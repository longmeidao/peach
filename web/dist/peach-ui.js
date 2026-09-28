import { dismissMenu as e, emptyStateHtml as t, loadingDotsHtml as n, moveGlidePane as r, noteHtml as i, presentMenu as a, scrollMovesAnchor as o, wireCollapse as s } from "/js/ui-components.js";
import { api as c, esc as l, fmtClock as u, fmtSize as d, icon as f, realDuration as p } from "/js/core.js";
//#region src/sort-preferences.ts
function m(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/number-setting.ts
var h = {
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
	let n = null, r = "", i = null, a, s = () => {
		clearTimeout(a), t.hidden = !0, n && (n.hasAttribute("title") || (n.title = r), i === null ? n.removeAttribute("aria-describedby") : n.setAttribute("aria-describedby", i)), n = null;
	}, c = (e, o) => {
		let c = e instanceof Element ? e.closest("[title]") : null;
		!c || c === n || c.closest(".vjs-control") || !c.title.trim() || (s(), n = c, r = c.title, i = c.getAttribute("aria-describedby"), c.removeAttribute("title"), a = setTimeout(() => {
			if (n !== c || !c.isConnected) return;
			t.textContent = r, t.hidden = !1;
			let e = c.getBoundingClientRect(), a = t.getBoundingClientRect();
			t.style.left = `${Math.max(8, Math.min(innerWidth - a.width - 8, e.left + (e.width - a.width) / 2))}px`, t.style.top = `${e.top >= a.height + 16 ? e.top - a.height - 8 : Math.min(innerHeight - a.height - 8, e.bottom + 8)}px`, c.setAttribute("aria-describedby", [i, t.id].filter(Boolean).join(" "));
		}, o));
	};
	document.addEventListener("pointerover", (e) => c(e.target, 400)), document.addEventListener("pointerout", (e) => {
		n && !n.contains(e.relatedTarget) && s();
	}), document.addEventListener("focusin", (e) => c(e.target, 0)), document.addEventListener("focusout", s), document.addEventListener("keydown", (e) => {
		e.key === "Escape" && s();
	}), document.addEventListener("scroll", (e) => {
		n && o(e, n) && s();
	}, !0), window.addEventListener("resize", s);
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
		let n = e.className + (e.getAttribute("aria-label") ?? ""), i = C.get(n) ?? null, a = () => {
			let a = e.querySelector("label:has(input:checked),button[aria-selected=true]");
			if (!a || !a.offsetWidth) return;
			let o = {
				x: a.offsetLeft,
				y: a.offsetTop,
				w: a.offsetWidth,
				h: a.offsetHeight
			};
			r(t, i, o, "x"), i = o, C.set(n, o);
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
	}), s(e, "details[data-sidebar-group]", "sidebar-collapse"), e.querySelectorAll(".board-section-toggle").forEach((e) => {
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
	return `<div class="board-job-progress" role="progressbar" aria-label="${l(e)}" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${r}"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle class="board-job-track" cx="18" cy="18" r="15"/><circle class="board-job-fill" cx="18" cy="18" r="15" pathLength="100" stroke-dasharray="${i} ${100 - i}" transform="rotate(-90 18 18)"/></svg><span>${l(e)}<small>${Math.round(i)}%</small></span></div>`;
}
function j(e, t = 0, r = 0) {
	return r > 0 ? A(e, t, r) : n(e);
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
function ee(e) {
	let t = e.note || ((e) => i(e, {
		label: "任务状态",
		variant: "error"
	})), r = e.loading || n, a = e.progress || ((e, t, n) => j(n || `已处理 ${e} / ${t}`, e, t)), o = e.container || ((e) => `<section class="followtask" data-geist-fieldset aria-label="任务进度"><div class="geist-fieldset-content">${e}</div></section>`), s = document.createElement("div");
	e.host.hidden = !0, s.dataset.followJob = "", s.setAttribute("aria-live", "polite"), e.host.prepend(s);
	let c = e.storageKey || "peach-follow-job", l = sessionStorage.getItem(c) || void 0, u = !1;
	M({
		read: e.read,
		active: () => !u && e.active() && s.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (n) => {
			let i = n.status === "running";
			if (e.host.hidden = !i, e.busy(i), i) {
				l = n.job_id, l && sessionStorage.setItem(c, l);
				let t = n.current, i = (t?.attempt || 1) > 1 ? ` · 第 ${t?.attempt}/${t?.max_attempts} 次尝试${t?.retry_in ? `，${t.retry_in} 秒后重试` : ""}` : "", u = (n.message || (e.title ? e.title + (n.total ? `：已完成 ${n.checked || 0}/${n.total}` : "") : "") || (n.total ? `${n.older ? "抓取历史" : "检查更新"}：已完成 ${n.checked || 0}/${n.total} 个来源` : "正在准备检查任务…")) + (t ? ` · ${t.label || t.provider || ""}${i}` : ""), d = (n.total || 0) > 0 ? a(n.checked || 0, n.total, u) : r(u);
				s.innerHTML = o(d);
			} else if (l && l === n.job_id) l = void 0, u = !0, e.host.hidden = n.status !== "failed", sessionStorage.removeItem(c), s.innerHTML = n.status === "failed" ? t(n.error || "检查失败") : "", e.complete(n);
			else {
				if (l && n.status === "idle") {
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
function te(e, t, n, r, i, a = i || !e.has(r)) {
	let o = n === null ? -1 : t.indexOf(n), s = t.indexOf(r);
	return i && o >= 0 && s >= 0 ? t.slice(Math.min(o, s), Math.max(o, s) + 1).forEach((t) => e.add(t)) : a ? e.add(r) : e.delete(r), r;
}
function N(e, t) {
	let n = t.filter((t) => e.has(t)).length;
	return {
		count: n,
		all: n > 0 && n === t.length,
		mixed: n > 0 && n < t.length
	};
}
function P(e, t, n) {
	t.forEach((t) => n ? e.add(t) : e.delete(t));
}
function ne({ count: e, label: t, all: n, summary: r, actions: i, locked: a = !1 }) {
	e && (e.textContent = t), n && (n.checked = r.all, n.indeterminate = r.mixed);
	for (let e of i) e.disabled = !r.count || a;
}
function re(e, t, n = 1) {
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
function ie(e, t) {
	return Math.max(1, Math.ceil(e / t));
}
function ae(e, t) {
	return Math.min(Math.max(1, Math.floor(e) || 1), t);
}
function oe(e, t, n) {
	if (t <= 1) return "";
	let r = re(e, t).map((t) => t === "…" ? "<li class=\"board-page-dots\" aria-hidden=\"true\">…</li>" : `<li><button type="button" class="board-page" data-page="${t}" aria-label="第 ${t} 页"${t === e ? " aria-current=\"page\"" : ""}>${t}</button></li>`).join("");
	return `<nav class="board-pagination" aria-label="${n}">
    <button type="button" class="geist-button" data-page="${e - 1}"${e <= 1 ? " disabled" : ""}><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-left"></use></svg>上一页</button>
    <ul>${r}</ul>
    <button type="button" class="geist-button" data-page="${e + 1}"${e >= t ? " disabled" : ""}>下一页<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"></use></svg></button>
  </nav>`;
}
//#endregion
//#region src/native-image.ts
function se(e, t, n, r) {
	if (!(e > 0 && t > 0 && n > 0 && r > 0)) return 0;
	let i = e / n, a = t / r;
	return i > 1.001 || a > 1.001 || Math.abs(i - a) > Math.max(i, a) * .01 ? 0 : i;
}
function ce(e, t, n, r, i = 1) {
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
function le(e, t, n) {
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
//#region src/follow-sort.ts
var ue = [
	["checked", "检查时间"],
	["added", "添加时间"],
	["name", "创作者名称"],
	["sources", "来源数量"],
	["source", "来源名称"],
	["provider", "站点"],
	["status", "状态"]
], de = "checked", fe = {
	checked: "desc",
	added: "desc",
	name: "asc",
	sources: "desc",
	source: "asc",
	provider: "asc",
	status: "asc"
}, pe = (e) => ue.some(([t]) => t === e);
function me(e, t) {
	let n = pe(e) ? e : de;
	return {
		sort: n,
		dir: t === "asc" || t === "desc" ? t : fe[n]
	};
}
//#endregion
//#region src/island-skeleton.ts
var he = "inline-flex items-center justify-center gap-0.5 whitespace-nowrap overflow-hidden font-sans", ge = {
	medium: "h-9 rounded-2lg p-2 text-body-medium",
	small: "h-8 rounded-lg px-2 py-1.5 text-body-medium"
}, _e = {
	medium: ge.medium,
	small: "size-8 rounded-lg p-0 text-body-medium"
}, ve = {
	medium: "size-5 shrink-0",
	small: "size-[18px] shrink-0"
}, ye = {
	medium: "inline-flex items-center justify-center px-1 shrink-0",
	small: "inline-flex items-center justify-center px-0.5 shrink-0"
}, be = {
	primary: "bg-button-primary text-text-white shadow-xs",
	secondary: "bg-background-primary-default text-text-primary border border-border-button-default shadow-xs",
	ghost: "bg-button-ghost-background text-button-ghost-foreground"
}, xe = (e, t) => `<svg class="${t}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><use href="#i-${e}"/></svg>`;
function F({ variant: e = "primary", size: t = "medium", glyph: n, label: r, attrs: i = "", compact: a = !1 }) {
	let o = r ? ge[t] : _e[t], s = n ? xe(n, ve[t]) : "", c = r ? `<span class="${ye[t]}"${a ? " data-compact-label" : ""}>${r}</span>` : "";
	return `<button type="button" class="${he} ${o} ${be[e]}"${i ? ` ${i}` : ""}>${s}${c}</button>`;
}
var Se = {
	md: {
		box: "gap-1.5 px-2.5 py-2 text-body-medium",
		value: "gap-[5px]",
		chevron: "size-4"
	},
	sm: {
		box: "gap-1 px-[7px] py-1 text-body-2-medium",
		value: "gap-1",
		chevron: "size-3.5"
	}
};
function Ce(e, { size: t = "md", className: n = "", attrs: r = "" } = {}) {
	let i = Se[t];
	return `<div class="group flex flex-col${n ? ` ${n}` : ""}"><button type="button" aria-haspopup="listbox"${r ? ` ${r}` : ""} class="flex w-full items-center justify-between rounded-2lg border border-border-button-default bg-background-primary-default shadow-xs text-text-primary ${i.box}"><span class="flex min-w-0 items-center truncate ${i.value}">${e}</span>${xe("chevron-down", `shrink-0 text-text-secondary ${i.chevron}`)}</button></div>`;
}
//#endregion
//#region src/board-skeleton.ts
var I = (e = "60%") => `<span class="skeleton" style="width:${e}"></span>`, L = () => `${I("80%")}${I("48%")}`, R = (e, t) => e.repeat(t), we = (e, t = "metricstrip") => `<div class="${t}">${e.map((e) => `<div class="tastesummary"><span class="board-stat-label">${e}</span><b class="board-stat-value">${I("45%")}</b><small class="board-stat-footer">${I("60%")}</small></div>`).join("")}</div>`, Te = (e, t = "skeleton-tabs") => `<div class="${t}">${e.map((e) => `<span>${e}</span>`).join("")}</div>`, Ee = (e, t) => `<div class="${t} skeleton-segments" data-board-segments="true">${e.map((e, t) => `<span${t === 0 ? " class=\"skeleton-segment-selected\"" : ""}>${e}</span>`).join("")}</div>`, z = (e) => `<section class="insightpanel"><header>${e}</header><div class="insightpanelbody skeleton-lines">${R(L(), 3)}</div></section>`, B = "disabled data-skeleton-action", V = (e) => `<span class="skeleton skeleton-text" style="width:${e}"></span>`, H = (e, t, n = !1) => `<span class="skeleton" style="width:${e}px;height:${t}px;flex:none${n ? ";border-radius:50%" : ""}"></span>`, De = "min-w-0 bg-background-secondary-default rounded-2xl shadow-card flex flex-col gap-3 px-6 py-5 max-sm:gap-2 max-sm:p-4", Oe = () => `<div class="inline-grid w-full grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 xl:grid-cols-6">${[
	"关注创作者",
	"启用来源",
	"检查失败",
	"未看更新",
	"JAV 订阅",
	"未看新作"
].map((e) => `<div class="${De}"><span class="text-body-medium text-text-secondary">${e}</span><b class="text-title-1-medium tabular-nums text-text-primary">${V("3em")}</b></div>`).join("")}</div>`, ke = "flex min-h-7 flex-none items-center gap-1.5 rounded-md px-2.5 py-1 text-body-medium whitespace-nowrap text-text-secondary data-selected:bg-background-primary-default data-selected:text-text-primary data-selected:shadow-card dark:data-selected:bg-background-primary-hover", Ae = () => `<div class="inline-flex w-max max-w-full items-center gap-0.5 overflow-x-auto overscroll-x-contain rounded-2lg bg-background-tertiary-default p-1">${[
	"关注列表",
	"添加关注",
	"JAV 订阅源",
	"来源和凭证"
].map((e, t) => `<span class="${ke}"${t === 0 ? " data-selected=\"true\"" : ""}>${e}</span>`).join("")}</div>`, je = (e = "") => `<span class="group inline-flex items-center select-none gap-2"><span class="flex shrink-0 items-center justify-center rounded-sm size-4 border bg-background-primary-default shadow-xs border-border-checkbox-default"></span>${e ? `<span class="text-body-medium text-text-primary">${e}</span>` : ""}</span>`, Me = ({ table: e, sort: t, dir: n }) => {
	let r = ue.find(([e]) => e === t)[1];
	return `<div class="flex flex-wrap items-center gap-2 follow-skeleton-toolbar"><h3 class="mr-auto text-title-2-medium text-text-primary">关注列表</h3><span class="text-body-2-regular text-text-secondary">${V("132px")}</span>${F({
		glyph: "refresh-cw",
		label: "检查全部",
		compact: !0,
		attrs: B
	})}<span data-button-group role="group">${F({
		variant: "ghost",
		glyph: "layout-grid",
		attrs: `aria-pressed="${!e}"`
	})}${F({
		variant: "ghost",
		glyph: "table",
		attrs: `aria-pressed="${e}"`
	})}</span>${Ce(r)}${F({
		variant: "secondary",
		glyph: n === "asc" ? "arrow-up" : "arrow-down"
	})}${e ? "" : F({
		variant: "secondary",
		glyph: "chevron-up",
		label: "全部收起",
		compact: !0,
		attrs: B
	})}</div>`;
}, Ne = () => `<span class="flex shrink-0 items-center gap-1">${F({
	variant: "secondary",
	size: "small",
	glyph: "refresh-cw",
	attrs: B
})}${F({
	variant: "secondary",
	size: "small",
	glyph: "trash",
	attrs: B
})}</span>`, Pe = () => `<div class="flex min-h-16 flex-wrap items-center gap-3 px-2 py-3 follow-skeleton-source">${je()}<span class="flex min-w-0 grow flex-col gap-0.5"><span class="text-body-medium">${V("8em")}</span></span><span class="flex shrink-0 items-center gap-1.5">${H(14, 14)}</span>${H(48, 24)}<span class="shrink-0 text-body-2-regular whitespace-nowrap text-text-secondary">${V("113px")}</span>${Ne()}</div>`, Fe = (e) => `<section class="min-w-0 bg-background-primary-default rounded-2xl shadow-card flex flex-col overflow-hidden p-2 follow-skeleton-author"><div class="flex flex-wrap items-center gap-3 px-2 py-2.5" data-follow-author-header data-open>${H(32, 32, !0)}<b class="min-w-0 grow text-body-medium break-words text-text-primary">${V("92px")}</b>${F({
	variant: "secondary",
	size: "small",
	glyph: "refresh-cw",
	attrs: B
})}<span class="flex shrink-0 items-center gap-1">${H(14, 14)}${H(14, 14)}</span>${F({
	variant: "secondary",
	size: "small",
	glyph: "check-check",
	label: "全选",
	attrs: B
})}${F({
	variant: "secondary",
	size: "small",
	glyph: "chevron-up",
	label: "收起",
	attrs: B
})}</div><div data-source-divider>${R(Pe(), e)}</div></section>`, Ie = () => {
	try {
		return Number(JSON.parse(localStorage.getItem("peach.settings.v1") || "{}").followPageSize) || 20;
	} catch {
		return 20;
	}
}, Le = [
	["select", ""],
	["author", "创作者"],
	["source", "来源"],
	["provider", "站点"],
	["status", "状态"],
	["checked", "上次检查"],
	["actions", ""]
], Re = {
	name: "author",
	source: "source",
	provider: "provider",
	status: "status",
	checked: "checked"
}, ze = "<svg viewBox=\"0 0 24 24\" fill=\"none\" aria-hidden=\"true\"><path d=\"M12.7071 15.2929C12.3166 15.6834 11.6834 15.6834 11.2929 15.2929L7.70711 11.7071C7.07714 11.0771 7.52331 10 8.41421 10H15.5858C16.4767 10 16.9229 11.0771 16.2929 11.7071L12.7071 15.2929Z\" fill=\"currentColor\"/></svg>", Be = (e, { sort: t, dir: n }) => `<div data-board-data-table data-follow-table class="follow-skeleton-table"><div class="w-full overflow-x-auto"><table class="bui-table bui-table-sm"><thead><tr>${Le.map(([e, r]) => r ? `<th><span class="flex items-center gap-0.5">${r}<span data-sort-indicator${Re[t] === e ? ` data-direction="${n === "asc" ? "ascending" : "descending"}"` : ""}>${ze}</span></span></th>` : "<th></th>").join("")}</tr></thead><tbody>${R(`<tr>${[
	je(),
	`<span class="flex min-w-0 items-center gap-2">${H(32, 32, !0)}${V("5em")}</span>`,
	V("10em"),
	`<span class="flex items-center gap-1.5">${H(14, 14)}${V("4em")}</span>`,
	H(48, 24),
	V("113px"),
	Ne()
].map((e) => `<td>${e}</td>`).join("")}</tr>`, e)}</tbody></table></div></div>`, Ve = (e, t) => `<div class="flex flex-wrap items-center justify-between gap-3"><span class="text-body-2-regular text-text-secondary">${V("111px")}</span>${Ce(`每页 ${t} ${e ? "条" : "位"}`, { size: "sm" })}${H(204, 32)}</div>`, He = (e) => {
	let t = e.followLayout === "table", n = me(e.followSort, e.followDir), r = e.followPageSize || Ie(), i = t ? Be(r, n) : `${je("全选本页")}<div class="flex flex-col gap-3">${Fe(3)}${Fe(4)}${Fe(3)}</div>`;
	return `<div class="peach-react"><div class="mx-auto flex w-full max-w-board flex-col gap-8">${Oe()}<div class="flex flex-col gap-6">${Ae()}<div class="flex flex-col gap-4"><div class="min-w-0 bg-background-secondary-default rounded-2xl shadow-card flex flex-col gap-4 px-6 py-5 max-sm:px-4 follow-skeleton-surface" data-layout="${t ? "table" : "default"}">${Me({
		table: t,
		...n
	})}${i}${Ve(t, r)}</div></div></div></div></div>`;
};
function Ue() {
	return `<div data-skeleton="detail" role="status" aria-label="正在读取作品详情"><div class="sgrid" aria-hidden="true"><div class="vwrap skeleton-detail-media skeleton"></div><aside class="side"><div class="sidecontent skeleton-lines">${I("85%")}${I("65%")}${R(L(), 4)}</div></aside></div></div>`;
}
function We(e, t = {}) {
	let n = "";
	if (e === "/stats") n = `<div class="insightpage statsdashboard"><header class="insighttoolbar">${I("38%")}</header>${we([
		"馆藏视频",
		"看过",
		"内容标签",
		"使用空间"
	])}${z("馆藏视频")}${z("内容标签")}</div>`;
	else if (e === "/taste") n = `<div class="tastepage"><header class="tastehead">${Ee(["浏览器记录", "Peach 内部"], "insightswitch")}${I("24%")}</header><div class="tastestate"></div>${we([
		"浏览记录",
		"口味维度",
		"浏览候选",
		"私有导出"
	], "tastesummaries")}<section class="tastehero"><div class="insightcopy"><span>浏览器画像</span><div class="skeleton skeleton-radar"></div></div><div class="tastebars skeleton-lines">${R(L(), 4)}</div></section>${z("口味分析")}<div class="board-activity-charts">${z("浏览活动")}${z("时间分布")}</div>${z("标签")}</div>`;
	else if (e === "/follow-manage") n = He(t);
	else if (e === "/configuration") n = `<div class="configpage">${Te([
		"通用",
		"媒体",
		"网络与访问",
		"更新与维护"
	])}<section class="configfieldset"><div class="geist-fieldset-content"><h3 class="geist-fieldset-title">开机自启</h3><div class="skeleton-lines">${R(`<div class="skeleton-setting">${I("35%")}<span class="skeleton skeleton-toggle"></span></div>`, 3)}</div></div><footer class="geist-fieldset-footer">${I("100px")}</footer></section></div>`;
	else if (e === "/activity") n = `<div class="activitypage">${[
		"正在进行",
		"被挡下的",
		"最近完成"
	].map((e) => `<section class="activitysection"><h3 class="geist-fieldset-title">${e}</h3><div class="activity-runs"><article class="cleanupfieldset activity-run"><div class="geist-fieldset-content skeleton-lines">${I("35%")}${L()}</div></article></div></section>`).join("")}</div>`;
	else if (e === "/duplicates") n = `<div class="review"><div class="collection-summary">${I("38%")}</div><div class="fsechead dupactions"><h3>批量保留</h3>${I("40%")}</div>${R(`<section class="dupgroup"><div class="duphead">${I("45%")}</div><div class="duplist">${R(`<div class="duprow"><span class="dupcover skeleton"></span><span class="dupmarks">${I()}</span><span class="dupname">${I("90%")}</span>${I()}${I()}${I()}<span class="duppath">${I("70%")}</span></div>`, 2)}</div></section>`, 2)}</div>`;
	else if (e === "/quality-goals") n = `<div class="quality-workspace"><div class="collection-summary"><strong>待升级</strong>${I("20%")}</div><div class="qualitylist">${R(`<article class="qualityitem"><span class="qualitycover skeleton"></span><div class="qualitybody skeleton-lines">${L()}</div><footer class="qualityactions">${I("80%")}</footer></article>`, 6)}</div></div>`;
	else if (e === "/playlists") n = `<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><div class="playlistcreate skeleton-lines"><span>新播放列表</span>${I("200px")}</div></header><div class="playlistcards">${R(`<article class="card playlistcard"><div class="mixstack"><div class="pic skeleton"></div></div><div class="mixmeta"><span class="mav skeleton"></span><div class="mixcopy skeleton-lines">${L()}</div></div></article>`, 6)}</div></section>`;
	else return "";
	return `<div class="board-page-skeleton" data-skeleton="board${e}" role="status" aria-label="正在读取页面"><div aria-hidden="true" inert>${n}</div></div>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var Ge = [
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
function Ke() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function qe(e, t) {
	let n = new URLSearchParams();
	for (let t of Ge) e[t] && n.set(t, e[t]);
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
function Je({ kind: e = "catalog", filtered: n = !1, jav: r = !1, configurable: i = !1, online: a = !1 } = {}) {
	let o = i ? "<button class=\"geist-button primary\" data-empty-settings>添加内容</button>" : "", s = "<a class=\"geist-button" + (!i || a ? " primary" : "") + "\" href=\"/follow-manage?tab=add\">添加关注</a>";
	if (n || r) return t("search", r ? "还没有符合条件的 JAV 作品" : "没有符合条件的内容", r ? "已扫描但尚未补充发行资料的视频可在全部内容中查看。" : "清除筛选或搜索条件后查看全部内容。", { actions: "<a class=\"geist-button primary\" href=\"/?loc=&thumb=0\">查看全部内容</a>" });
	if (e !== "catalog") {
		let n = (a ? {
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
		return t(e === "tags" ? "tags" : "user-round", "还没有" + n, a ? "添加关注来源并获取内容后，这里会显示来源上的" + n + "。" : "添加内容并补充资料后，这里会显示对应信息。", { actions: a ? s : o + s });
	}
	return t("play", "还没有视频", "添加媒体文件夹或关注来源，开始建立你的馆藏。", { actions: o + s });
}
//#endregion
//#region src/sidebar.ts
function Ye(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function Xe(e, t) {
	return e.dataset.surface?.split("?")[0] === t.split("?")[0] && e.querySelector(".dnav") ? (e.dataset.surface = t, !1) : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function Ze(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
var Qe = "扫描媒体文件夹，导入已有资料，采集缺失信息。两段也可以分开跑：新盘刚接上时先只扫描，几万个文件登记完就能用；采集被网络拖住时只重跑采集，不必再扫一遍磁盘。", $e = "修缺时间戳表（播放卡顿）和缺索引（打不开）的 MP4。常看的片子先修。", U = "<span class=\"skeleton skeleton-text\" aria-hidden=\"true\"></span>", et = "type=\"button\" disabled data-skeleton-action", tt = "disabled data-skeleton-action", nt = "aria-disabled=\"true\"", rt = (e) => `<div class="peach-react"><div class="flex flex-col gap-4">${e}</div></div>`, it = (e, t) => `<div data-geist-fieldset-content>
          <h3 class="text-title-2-medium text-text-primary">${e}</h3>
          <p class="text-body-2-regular text-text-secondary">${t}</p></div>`;
function at() {
	return rt(`<section aria-label="扫描与采集" data-geist-fieldset data-cleanup-task data-cleanup-processing>
        ${it("扫描与采集", Qe)}
        <footer data-geist-fieldset-footer><a href="/scraping" class="inline-flex items-center justify-center gap-1 whitespace-nowrap font-sans rounded-sm text-body-medium text-accent-600"><span>来源和凭证</span>${xe("arrow-up", "size-[18px] shrink-0 rotate-90")}</a><span data-button-group data-split-button data-variant="primary">${F({
		glyph: "database",
		label: "扫描并补全资料",
		attrs: tt
	})}${F({
		glyph: "chevron-down",
		attrs: `${tt} aria-label="更多扫描与采集方式"`
	})}</span></footer>
      </section>`);
}
function ot() {
	return rt(`<section aria-label="媒体修复" data-geist-fieldset data-cleanup-task data-cleanup-processing>
        ${it("媒体修复", $e)}
        <footer data-geist-fieldset-footer>${Ce(U, {
		className: "w-48",
		attrs: nt
	})}${F({
		label: "开始修复",
		attrs: tt
	})}</footer>
      </section>`);
}
function st() {
	let e = [
		["人工复核", "square-check-big"],
		["高清版", "sparkles"],
		["重复文件", "file-stack"],
		["垃圾文件", "file-archive"],
		["回收站", "trash"]
	], t = `<span class="geist-button organize-preset-skeleton">${U}</span>`.repeat(3), n = (e) => `<div class="organizefield"><span>${e}</span>
            <span class="geist-input organize-input-skeleton">${U}</span></div>`;
	return `<div class="cleanuppage" data-skeleton="cleanup" aria-busy="true" aria-label="正在读取数据管理状态">
    <div class="cleanupstats">${e.map(([e, t]) => `
      <button type="button" class="board-plain-stat" disabled>
        <span class="board-plain-stat-head"><span class="board-stat-tile">${f(t)}</span>${e}</span>
        <strong>${U}</strong><span class="cleanupmeta">${U}</span></button>`).join("")}</div>
    <div class="cleanupgrid">
      <div class="cleanupscraping">${at()}</div>
      <div class="cleanupmediarepair">${ot()}</div>
      <section class="cleanupfieldset cleanuporganize" data-geist-fieldset data-cleanup-task aria-labelledby="cleanup-loading-organize">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-organize">整理</h3>
          <p>按模板给文件改名并归入目录。先预览，确认后执行；执行过的一批可以整批退回。</p>
          <div class="organizefields">
            <div class="organizesource"><span class="gselect"><span class="gselectfield organize-source-skeleton">${U}${f("chevron-down")}</span></span></div>
            ${n("文件名模板")}
            ${n("目录模板")}
            <div class="organizepresets">${t}</div>
            <p class="cleanupmeta">${U}</p>
          </div></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button class="geist-button primary" ${et}>预览</button></footer>
      </section></div>
    <section class="resourcesync" aria-labelledby="cleanup-loading-links">
      <h2 id="cleanup-loading-links">链接管理</h2>
      <div class="resourcesyncbox" data-geist-fieldset data-cleanup-task>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">站外链接</h3>
          <div class="linksummary"><div class="linkstats"><div><span>链接总数</span><b>${U}</b><small>${U}</small></div>${[
		"官网/事务所",
		"社交账号",
		"作品资料站"
	].map((e) => `<div><span>${e}</span><b>${U}</b></div>`).join("")}</div>
          <div class="linkhosts"><span>主要站点</span><b>${U}</b></div></div></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" ${et}>${f("unlink")}<span>检查死链</span></button></div>
      </div></section>
    <section class="resourcesync" aria-labelledby="cleanup-loading-sync">
      <h2 id="cleanup-loading-sync">资源同步</h2>
      <div class="resourcesyncbox" data-geist-fieldset data-cleanup-task>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">文件与记录核对</h3>
          <p>按馆藏记录逐条查找本地磁盘与网盘上的文件，列出文件已不存在的记录、空文件夹，以及不再被引用的缓存。</p></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" ${et}>${f("git-compare")}<span>检查文件</span></button></div>
      </div></section></div>`;
}
//#endregion
//#region src/junk-queue.ts
var ct = [
	[
		"",
		"全部",
		"layout-grid"
	],
	[
		"video",
		"视频",
		"play"
	],
	[
		"image",
		"图片",
		"pics"
	],
	[
		"archive",
		"压缩包",
		"file-archive"
	],
	[
		"audio",
		"音频",
		"file-audio"
	],
	[
		"url",
		"网址",
		"globe"
	],
	[
		"other",
		"其它",
		"hard-drive"
	]
], lt = (e) => ct.find(([t]) => t === e)?.[0] ?? "";
function ut(e) {
	let t = new URLSearchParams(e);
	return {
		kind: lt(t.get("type")),
		view: t.get("view") === "dismissed" ? "dismissed" : "pending"
	};
}
function dt(e = "", t = "pending") {
	let n = new URLSearchParams();
	e && n.set("type", e), t === "dismissed" && n.set("view", "dismissed");
	let r = n.toString();
	return `/junk-files${r ? `?${r}` : ""}`;
}
function ft(e) {
	return e === "dismissed" ? {
		view: "pending",
		label: "返回待判断",
		glyph: "rotate-ccw",
		href: dt("", "pending")
	} : {
		view: "dismissed",
		label: "已排除",
		glyph: "eye-off",
		href: dt("", "dismissed")
	};
}
var pt = (e) => e === "dismissed" ? "已排除" : "待判断", mt = "flex items-end justify-between gap-4 rounded-surface bg-background-secondary-default px-6 py-5 max-compact:flex-col max-compact:items-start max-compact:gap-3 max-compact:p-4 dark:bg-background-primary-default", ht = "flex min-w-0 flex-col gap-2", gt = "text-body-regular text-text-secondary", _t = "text-display-4-medium tabular-nums text-text-primary", vt = "relative inline-block h-8 w-24 rounded-2lg align-middle skeleton-sheen", yt = (e) => `<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-${e}"></use></svg>`;
function bt({ kind: e, view: t }) {
	let n = ct.map(([n, r, i]) => `<a href="${dt(n, t)}" data-junk-kind-link="${n}"${n === e ? " aria-current=\"page\"" : ""}>${yt(i)}${l(r)}</a>`).join(""), r = ft(t);
	return `<div class="peach-react" data-junk-count-skeleton=""><div data-junk-count=""><div data-junk-summary="" aria-live="polite"><div data-collection-summary="" class="${mt}"><div class="${ht}"><span class="${gt}">${pt(t)}</span><strong class="${_t}"><span data-skeleton="count" aria-hidden="true" class="${vt}"></span></strong></div></div></div><div data-junk-filters-frame=""><nav data-junk-filters="" aria-label="垃圾文件分类">${n}<i data-junk-divider="" aria-hidden="true"></i><a href="${r.href}" data-junk-view-link="${r.view}"${t === "dismissed" ? " aria-current=\"page\"" : ""}>${yt(r.glyph)}${r.label}</a></nav></div></div></div>`;
}
//#endregion
//#region src/jav-artwork.ts
function xt(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function St(e) {
	return {
		javLayout: xt(e.javLayout),
		javImage: Ct(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function Ct(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function wt(e, t) {
	return e.is_jav && e.code && e.has_cover && (Ct(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function Tt(e, t) {
	let n = Number(e?.px?.[0]), r = Number(e?.px?.[1]), i = Number(e?.x0);
	if (!(n > 0 && r > 0 && t > 0) || !Number.isFinite(i)) return null;
	let a = (e, t, n) => Math.min(n, Math.max(0, Number.isFinite(Number(e)) ? Number(e) : t)), o = a(i, 0, n), s = Math.max(o, a(e?.x1, n, n)), c = a(e?.y0, 0, r), l = Math.max(c, a(e?.y1, r, r)), u = s - o, d = l - c;
	if (!(u > 0 && d > 0)) return null;
	let f = u / d / t;
	if (!(f > 0)) return null;
	let p = f <= 1 ? (1 - f) / 2 - o / d / t : 1 - s / d / t, m = (e) => (Math.round(e * 1e4) || 0) / 100;
	return {
		clip: {
			top: m(c / r),
			right: m(1 - s / n),
			bottom: m(1 - l / r),
			left: m(o / n)
		},
		left: m(p),
		top: m(-c / d),
		height: m(r / d)
	};
}
function Et(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (Ct(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.classList.remove("panel"), e.removeAttribute("style"), e.closest(".pic,[data-media-pic]")?.style.removeProperty("--cover-blur"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
function Dt(e, t) {
	let n = [];
	return e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		e.dataset.javImageLayout !== t && (e.dataset.javImageLayout = t, e.classList.contains("cover") && (e.classList.toggle("whole", t !== "big"), e.classList.toggle("front", t === "big"), e.classList.remove("panel"), e.removeAttribute("style"), e.closest(".pic,[data-media-pic]")?.style.removeProperty("--cover-blur"), e.complete && e.naturalWidth && n.push(e)));
	}), n;
}
//#endregion
//#region src/player/host.ts
var Ot = null;
function kt(e) {
	Ot = e;
}
function W() {
	if (!Ot) throw Error("播放器还没有接上宿主（configurePlayer）");
	return Ot;
}
//#endregion
//#region src/player/menu.ts
var G = null;
function At(e) {
	G = e;
}
var jt = () => document.getElementById("playerMenu"), Mt = null;
function K() {
	let t = jt();
	t?.matches(":popover-open") && t.hidePopover(), t && t.parentElement !== document.body && document.body.append(t), t && e(t, () => {
		t.innerHTML = "";
	}), Mt &&= (Mt(), null);
}
async function Nt(e) {
	try {
		return await navigator.clipboard.writeText(e), !0;
	} catch {
		let t = document.createElement("textarea");
		t.value = e, t.setAttribute("readonly", ""), t.style.position = "fixed", t.style.opacity = "0", document.body.append(t), t.select();
		let n = !1;
		try {
			n = document.execCommand("copy");
		} catch {}
		return t.remove(), n;
	}
}
function Pt(e) {
	let t = !!G?.inMiniplayer(e), n = e.peachItem, r = G?.kind(e) ?? "item", i = (t) => {
		let i = new URL(r === "follow" ? `/follow/item/${n?.id}` : `/item/${n?.id}`, location.origin);
		return t && i.searchParams.set("t", String(Math.floor(e.currentTime() || 0))), i.href;
	}, a = (e, t) => {
		Nt(i(e)).then((e) => W().toast(e ? t : "复制失败，请手动复制地址栏", {
			timeout: 4e3,
			warn: !e
		}));
	}, o = [{
		icon: "repeat",
		label: "循环播放",
		checked: !!e.loop(),
		run: () => e.loop(!e.loop())
	}, t ? {
		icon: "maximize-2",
		label: "展开",
		run: () => G?.expand()
	} : {
		icon: "picture-in-picture-2",
		label: "迷你播放器",
		run: () => G?.toMiniplayer()
	}];
	document.pictureInPictureEnabled && o.push({
		icon: "player-pip",
		fill: !0,
		label: "画中画",
		run: () => e.el().querySelector(".vjs-picture-in-picture-control")?.click()
	}), o.push({
		icon: "link",
		label: "复制视频网址",
		run: () => a(!1, "已复制视频网址")
	}), o.push({
		icon: "link",
		label: "复制当前时间的视频网址",
		run: () => a(!0, "已复制当前时间的视频网址")
	});
	let s = document.getElementById("playerStatsBtn");
	return !t && s && !s.hidden && o.push({
		icon: "chart",
		label: "播放统计",
		run: () => s.click()
	}), o;
}
function Ft(e, t, n) {
	let r = jt();
	if (!r) return;
	K();
	let i = W().stage();
	i instanceof HTMLDialogElement && i.open && i.append(r), r.setAttribute("popover", "manual");
	let s = Pt(e);
	r.innerHTML = s.map((e, t) => {
		let n = e.checked !== void 0;
		return `<button type="button" class="playermenuitem" role="${n ? "menuitemcheckbox" : "menuitem"}"${n ? ` aria-checked="${e.checked}"` : ""} data-player-menu="${t}">${f(e.icon, e.fill ? "playermenufill" : "")}<span>${l(e.label)}</span>${n ? f("check", "playermenucheck") : ""}</button>`;
	}).join(""), a(r), r.showPopover(), r.style.left = `${Math.max(8, Math.min(t, innerWidth - r.offsetWidth - 8))}px`, r.style.top = `${Math.max(8, Math.min(n, innerHeight - r.offsetHeight - 8))}px`;
	let c = [...r.querySelectorAll("[data-player-menu]")];
	c.forEach((e) => {
		e.onclick = (t) => {
			t.stopPropagation();
			let n = s[Number(e.dataset.playerMenu)];
			K(), n?.run();
		};
	});
	let u = (e) => {
		r.contains(e.target) || K();
	}, d = (e) => {
		if (e.key === "Escape") {
			e.stopPropagation(), K();
			return;
		}
		if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
		e.preventDefault();
		let t = c.indexOf(document.activeElement);
		c[(t + (e.key === "ArrowDown" ? 1 : -1) + c.length) % c.length]?.focus();
	}, p = (t) => {
		o(t, e.el()) && K();
	};
	setTimeout(() => {
		document.addEventListener("pointerdown", u, !0), document.addEventListener("keydown", d, !0), window.addEventListener("scroll", p, {
			capture: !0,
			passive: !0
		});
	}, 0), Mt = () => {
		document.removeEventListener("pointerdown", u, !0), document.removeEventListener("keydown", d, !0), window.removeEventListener("scroll", p, !0);
	}, c[0]?.focus();
}
function It(e) {
	e.el().addEventListener("contextmenu", (t) => {
		t.target.closest(".vjs-peach-settings-menu") || (t.preventDefault(), Ft(e, t.clientX, t.clientY));
	}), e.on("dispose", K);
}
//#endregion
//#region src/player/registry.ts
var Lt = null, q = () => Lt;
function Rt(e) {
	Lt = e;
}
function zt(e) {
	!e || e.isDisposed() || requestAnimationFrame(() => {
		e.isDisposed() || e.trigger("resize");
	});
}
//#endregion
//#region src/player/stats.ts
function Bt(e) {
	let t = e.currentTime || 0;
	for (let n = 0; n < e.buffered.length; n++) if (e.buffered.start(n) <= t && e.buffered.end(n) >= t) return Math.max(0, e.buffered.end(n) - t);
	return 0;
}
function Vt(e) {
	let t = e.currentTime || 0;
	for (let n = 0; n < e.buffered.length; n++) if (e.buffered.start(n) <= t + .25 && e.buffered.end(n) >= t) return e.buffered.end(n);
	return e.buffered.length ? e.buffered.end(e.buffered.length - 1) : 0;
}
var Ht = 3e3;
function Ut(e, t) {
	let n = Number(e) || 0, r = p(t) || 0;
	return n > 0 && r > 0 ? n * 8 / r : 0;
}
function Wt(e) {
	let t = [], n = null, r = 0, i = 0;
	return {
		bitrate: Number(e) || 0,
		get bits() {
			return i;
		},
		get seconds() {
			return r;
		},
		bytes() {
			return this.bitrate > 0 ? r * this.bitrate / 8 : 0;
		},
		sample(e) {
			if (!e) return i;
			let a = performance.now(), o = Vt(e), s = e.currentTime || 0;
			if (n) {
				let e = (a - n.at) / 1e3, i = Math.abs(s - n.ct) > e * 4 + 1, c = o - n.frontier;
				!i && c > 0 && (r += c), e * 1e3 > Ht * 2 && (t.length = 0);
			}
			for (n = {
				at: a,
				frontier: o,
				ct: s
			}, t.push({
				at: a,
				advanced: r
			}); t.length > 2 && a - t[0].at > Ht;) t.shift();
			let c = t[0], l = (a - c.at) / 1e3, u = r - c.advanced;
			return l >= .5 && u > 0 && this.bitrate > 0 && (i = u * this.bitrate / l), i;
		}
	};
}
var Gt = 24;
function Kt(e, t) {
	e.push(Number.isFinite(t) && t > 0 ? t : 0), e.length > Gt && e.splice(0, e.length - Gt);
}
var J = "peach-player-panel";
function qt(e, t, n, r) {
	let i = [...Array(Math.max(0, Gt - e.length)).fill(null), ...e], a = Math.max(1, n || 0), o = i.map((e) => {
		if (e === null) return "<i aria-hidden=\"true\"></i>";
		let n = e <= 0 ? 0 : Math.max(.08, Math.min(1, e / a));
		return `<i class="active${t === "buffer" ? e < 5 ? " low" : e < 15 ? " mid" : " good" : ""}" style="height:${(n * 100).toFixed(1)}%" aria-hidden="true"></i>`;
	}).join("");
	return `<span class="playerstatsplot ${t}" role="img" aria-label="${l(r)}">${o}</span>`;
}
function Jt() {
	return `<button class="playerstatsbtn" id="playerStatsBtn" aria-label="播放统计" title="播放统计" aria-pressed="false" hidden>${f("chart")}</button>
       <div class="playernet" id="playerNet" role="status" aria-live="polite" hidden></div>
       <div class="playerstats" id="playerStats" role="status" hidden></div>`;
}
function Yt(e, t = "") {
	let n = t ? encodeURIComponent(t) : "";
	return performance.getEntriesByType("resource").filter((t) => t.name.includes("/stream") && (t.name.includes(`/stream?id=${e}`) || t.name.includes(`/stream/hls/${e}/`)) && (!n || t.name.includes(`session=${n}`)));
}
function Xt(e, t = "") {
	let n = Yt(e, t), r = n.reduce((e, t) => e + (t.transferSize || t.encodedBodySize || 0), 0), i = n.reduce((e, t) => e + (t.duration || 0), 0) / 1e3;
	return r > 0 && i > 0 ? r * 8 / i : 0;
}
function Zt(e, t, n = "", r = null) {
	let i = 0;
	try {
		i = Number(e?.tech({ IWillNotUseThisInPlugins: !0 })?.vhs?.stats?.bandwidth) || 0;
	} catch {}
	return i > 0 ? i : r ? Number(r.bits) || 0 : Xt(t, n);
}
function Qt(e) {
	if (!Number.isFinite(e) || e <= 0) return "加载中…";
	let t = e / 8;
	return t >= 1048576 ? `${(t / 1048576).toFixed(1)} MB/s` : `${Math.max(1, Math.round(t / 1024))} KB/s`;
}
function $t(e, t) {
	return e > 0 ? Qt(e) : t > 0 ? `已缓冲 ${Math.round(t)} 秒` : Qt(0);
}
//#endregion
//#region src/player/controls.ts
function Y(e, t, n = "") {
	if (!e) return () => {};
	let r = e.querySelector(":scope>.vjs-peach-tooltip");
	r || (r = document.createElement("span"), r.className = "vjs-peach-tooltip", r.setAttribute("role", "tooltip"), r.innerHTML = "<span class=\"vjs-peach-tooltip-text\"></span><kbd hidden></kbd>", e.append(r));
	let i = r.querySelector(".vjs-peach-tooltip-text"), a = r.querySelector("kbd");
	n && e.setAttribute("aria-keyshortcuts", n);
	let o = (r = t, o = "") => {
		i.textContent = r, a.textContent = n, a.hidden = !n, e.setAttribute("aria-label", o || r), e.removeAttribute("title");
	};
	return o(), o;
}
function en(e, t) {
	e?.closest(".video-js")?.querySelector(`.vjs-control-bar ${t}`)?.click();
}
function tn(e, t = !0) {
	let n = W(), r = n.settings();
	r.ambientMode = !!e, t && n.saveSettings(), n.stage()?.classList.toggle("ambient-on", r.ambientMode), document.dispatchEvent(new CustomEvent("peachambientchange", { detail: { enabled: r.ambientMode } }));
}
var nn = /* @__PURE__ */ new WeakMap();
function rn(e) {
	if (!e) return;
	let t = W().settings().theaterMode;
	e.setAttribute("aria-pressed", String(t)), e.querySelector("use")?.setAttribute("href", t ? "#i-theater-exit" : "#i-theater-enter"), nn.get(e)?.(t ? "默认视图" : "影院模式");
}
function an(e, t = !0) {
	let n = W(), r = n.settings();
	r.theaterMode = !!e, t && n.saveSettings();
	let i = n.stage();
	i?.classList.toggle("theater-mode", r.theaterMode), rn(i?.querySelector("[data-player-theater]")), zt(q());
}
function on(e) {
	let t = W().stage(), n = t?.querySelector(".ambientcanvas");
	if (!t || !n) return () => {};
	let r = n.getContext("2d", { alpha: !1 });
	if (!r) return () => {};
	let i = !1, a = 0, o = 0, s = () => {
		r.clearRect(0, 0, n.width, n.height), t.style.removeProperty("--video-glow");
	}, c = () => {
		if (!(e.readyState < 2)) try {
			r.drawImage(e, 0, 0, n.width, n.height);
			let i = r.getImageData(0, 0, n.width, n.height).data, a = 0, o = 0, s = 0, c = 0;
			for (let e = 0; e < i.length; e += 16) a += i[e], o += i[e + 1], s += i[e + 2], c++;
			c && t.style.setProperty("--video-glow", `rgb(${Math.round(a / c)} ${Math.round(o / c)} ${Math.round(s / c)})`);
		} catch {}
	}, l = (t) => {
		e.requestVideoFrameCallback ? e.requestVideoFrameCallback((e) => u(t, e)) : requestAnimationFrame((e) => u(t, e));
	}, u = (t, n) => {
		if (!(i || t !== o)) {
			if (!W().settings().ambientMode) {
				s();
				return;
			}
			e.paused || (!document.hidden && n - a > 480 && (a = n, c()), l(t));
		}
	}, d = () => {
		i || !W().settings().ambientMode || (c(), e.paused || l(++o));
	}, f = (e) => {
		let n = !!e.detail.enabled;
		t.classList.toggle("ambient-on", n), n ? d() : (o++, s());
	};
	return document.addEventListener("peachambientchange", f), e.addEventListener("play", d), e.addEventListener("loadeddata", d), d(), () => {
		i = !0, o++, document.removeEventListener("peachambientchange", f), e.removeEventListener("play", d), e.removeEventListener("loadeddata", d), s();
	};
}
function sn(e, t, n = 0, r = null) {
	let i = e.getChild("controlBar")?.el();
	if (!i || i.querySelector("[data-player-quality]")) return;
	let a = document.createElement("div");
	a.className = "vjs-peach-settings vjs-control", a.dataset.playerQuality = "", a.innerHTML = `<button type="button" class="vjs-peach-settings-toggle" aria-label="播放器设置" aria-expanded="false">
    ${f("settings")}<span data-player-quality-badge hidden></span></button>
    <div class="vjs-peach-settings-menu" role="menu" aria-label="播放器设置" aria-hidden="true"></div>`;
	let o = i.querySelector(".vjs-fullscreen-control");
	i.insertBefore(a, o || null);
	let s = a.querySelector("button"), c = a.querySelector("[data-player-quality-badge]");
	Y(s, "设置");
	let u = a.querySelector(".vjs-peach-settings-menu"), d = typeof e.qualityLevels == "function" ? e.qualityLevels() : null, p = r, m = "auto", h = (e, t) => {
		let n = [Number(e), Number(t)].filter((e) => e > 0);
		return n.length ? Math.min(...n) : 0;
	}, g = () => {
		let e = [];
		if (d?.length) {
			e.push({
				key: "auto",
				label: "自动",
				pixels: 0
			});
			for (let t = 0; t < d.length; t++) {
				let n = d[t], r = h(n.width, n.height);
				e.push({
					key: String(t),
					label: r ? `${r}p` : n.id || `线路 ${t + 1}`,
					pixels: r
				});
			}
			return e;
		}
		if (p?.length) return p.map((e) => ({
			key: `h${e.height}`,
			label: e.label || `${e.height}p`,
			pixels: e.height
		}));
		let r = h(t.videoWidth, t.videoHeight) || Number(n) || 0;
		return [{
			key: "original",
			label: r ? `${r}p` : "原画",
			pixels: r
		}];
	}, _ = () => {
		let e = g();
		!d?.length && !p?.length && (m = "original");
		let t = e.find((e) => e.key === m) || e[0], n = t.pixels || Math.max(0, ...e.map((e) => e.pixels || 0));
		return c.textContent = n >= 2160 ? "4K" : n >= 720 ? "HD" : "", c.hidden = !c.textContent, {
			options: e,
			active: t
		};
	}, v = () => u.getAttribute("aria-hidden") !== "true", y = (e) => {
		u.setAttribute("aria-hidden", String(!e)), s.setAttribute("aria-expanded", String(e)), e && document.dispatchEvent(new CustomEvent(J, { detail: "settings" }));
	}, b = () => y(!1), x = (e) => {
		e.detail !== "settings" && b();
	};
	document.addEventListener(J, x);
	let S = null, C = (e, t) => {
		let n = u.querySelector(".vjs-peach-panel"), r = document.createElement("div");
		if (r.className = "vjs-peach-panel", r.innerHTML = e, !n || !t || !v()) return u.replaceChildren(r), u.style.height = "", r;
		S &&= (clearTimeout(S), null);
		let i = u.getBoundingClientRect().height;
		n.classList.add("vjs-peach-panel-leaving"), r.classList.add(t > 0 ? "vjs-peach-panel-animate-forward" : "vjs-peach-panel-animate-back"), u.append(r), u.style.height = `${i}px`;
		let a = r.scrollHeight;
		return requestAnimationFrame(() => {
			u.classList.add("vjs-peach-popup-animating"), u.style.height = `${a}px`, r.classList.remove("vjs-peach-panel-animate-forward", "vjs-peach-panel-animate-back"), n.classList.add(t > 0 ? "vjs-peach-panel-animate-back" : "vjs-peach-panel-animate-forward"), S = setTimeout(() => {
				S = null, n.remove(), u.classList.remove("vjs-peach-popup-animating"), u.style.height = "";
			}, 250);
		}), r;
	}, w = (e, t) => e.querySelector(t), T = (t = 0) => {
		let { active: n } = _(), r = Number(e.playbackRate()) || 1, i = C(`<div class="vjs-peach-panel-menu"><button type="button" class="vjs-peach-menu-row" role="menuitemcheckbox" data-player-ambient aria-checked="${W().settings().ambientMode}">
      ${f("player-ambient")}<span>氛围模式</span><i class="vjs-peach-switch" aria-hidden="true"></i></button>
      <button type="button" class="vjs-peach-menu-row" role="menuitem" data-player-speed>${f("player-speed")}<span>播放速度</span><b>${r === 1 ? "正常" : `${r}×`}</b>${f("player-menu-next")}</button>
      <button type="button" class="vjs-peach-menu-row" role="menuitem" data-player-quality-view>${f("player-quality")}<span>清晰度</span><b>${l(n.label)}</b>${f("player-menu-next")}</button></div>`, t);
		w(i, "[data-player-ambient]").onclick = () => {
			tn(!W().settings().ambientMode), T();
		}, w(i, "[data-player-speed]").onclick = () => k(), w(i, "[data-player-quality-view]").onclick = () => A();
	}, E = .05, D = [
		1,
		1.25,
		1.5,
		2,
		3
	], O = (e) => Number.isInteger(e) ? e.toFixed(1) : String(e), k = (t = 1) => {
		let n = .25, r = (e) => Math.min(3, Math.max(n, Number(e.toFixed(2)))), i = C(`<div class="vjs-peach-panel-header"><button type="button" class="vjs-peach-menu-back" data-player-menu-back aria-label="返回上一个菜单">${f("player-menu-back")}</button><strong>播放速度</strong></div>
      <div class="vjs-peach-speed-panel"><div class="vjs-peach-speed-display"><output data-player-speed-display></output></div>
      <div class="vjs-peach-speed-slider"><button type="button" class="vjs-peach-speed-button" data-player-speed-step="-1" aria-label="播放速度减 0.05">${f("minus")}</button>
      <input type="range" class="vjs-peach-speed-range" data-player-speed-range min="${n}" max="3" step="${E}" aria-label="播放速度">
      <button type="button" class="vjs-peach-speed-button" data-player-speed-step="1" aria-label="播放速度加 0.05">${f("plus")}</button></div>
      <div class="vjs-peach-speed-chips">${D.map((e) => `<span class="vjs-peach-speed-preset"><button type="button" class="vjs-peach-speed-button" data-player-speed-option="${e}" aria-pressed="false">${O(e)}</button>${e === 1 ? "<span class=\"vjs-peach-speed-preset-label\">正常</span>" : ""}</span>`).join("")}</div></div>`, t), a = i.querySelector("[data-player-speed-display]"), o = i.querySelector("[data-player-speed-range]"), s = r(Number(e.playbackRate()) || 1), c = () => {
			a.textContent = `${s.toFixed(2)}x`, o.value = String(s), o.style.setProperty("--peach-speed-percent", `${(s - n) / 2.75 * 100}%`), i.querySelectorAll("[data-player-speed-option]").forEach((e) => e.setAttribute("aria-pressed", String(Number(e.dataset.playerSpeedOption) === s)));
		}, l = (t) => {
			s = r(t), e.playbackRate(s), c();
		};
		w(i, "[data-player-menu-back]").onclick = () => T(-1), o.oninput = () => l(Number(o.value)), i.querySelectorAll("[data-player-speed-step]").forEach((e) => {
			e.onclick = () => l(s + Number(e.dataset.playerSpeedStep) * E);
		}), i.querySelectorAll("[data-player-speed-option]").forEach((e) => {
			e.onclick = () => l(Number(e.dataset.playerSpeedOption));
		}), c();
	}, A = (n = 1) => {
		let { options: r } = _(), i = C(`<div class="vjs-peach-panel-header"><button type="button" class="vjs-peach-menu-back" data-player-menu-back aria-label="返回上一个菜单">${f("player-menu-back")}</button><strong>清晰度</strong></div><div class="vjs-peach-panel-menu">${r.map((e) => `<button type="button" class="vjs-peach-menu-option" role="menuitemradio" data-player-quality-option="${l(e.key)}" aria-checked="${e.key === m}"><span class="vjs-peach-option-check">${e.key === m ? f("player-option-check") : ""}</span><span class="vjs-peach-option-label">${l(e.label)}</span></button>`).join("")}</div>`, n);
		w(i, "[data-player-menu-back]").onclick = () => T(-1), i.querySelectorAll("[data-player-quality-option]").forEach((n) => {
			n.onclick = () => {
				if (m = n.dataset.playerQualityOption || "auto", d?.length) for (let e = 0; e < d.length; e++) d[e].enabled = m === "auto" || m === String(e);
				if (p?.length && m.startsWith("h")) {
					let n = m.slice(1), r = e.currentTime() || 0, i = !e.paused(), a = new URL(e.currentSrc() || t.src, location.origin);
					a.searchParams.set("quality", n), e.src({
						src: a.pathname + a.search,
						type: "video/mp4"
					}), e.one("loadedmetadata", () => {
						r > 0 && e.currentTime(r), i && e.play()?.catch(() => {});
					});
				}
				T(-1);
			};
		});
	};
	s.onclick = (e) => {
		e.stopPropagation();
		let t = !v();
		t && T(), y(t);
	};
	let j = (e) => {
		a.contains(e.target) || b();
	};
	return document.addEventListener("pointerdown", j), a.addEventListener("keydown", (e) => {
		e.key === "Escape" && (b(), s.focus());
	}), t.addEventListener("loadedmetadata", () => {
		v() ? T() : _();
	}), d?.on?.(["addqualitylevel", "removequalitylevel"], () => {
		v() ? T() : _();
	}), e.on("dispose", () => {
		document.removeEventListener("pointerdown", j), document.removeEventListener(J, x), S && clearTimeout(S);
	}), _(), cn(e, a), ln(e), (e) => {
		p = e?.length ? e : null, v() ? T() : _();
	};
}
function cn(e, t) {
	let n = e.getChild("controlBar")?.el();
	if (!n || n.querySelector("[data-player-theater]")) return;
	let r = W().settings().theaterMode, i = document.createElement("div");
	i.className = "vjs-peach-theater vjs-control", i.innerHTML = `<button type="button" data-player-theater aria-pressed="${r}">${f(r ? "theater-exit" : "theater-enter")}</button>`, n.insertBefore(i, t.nextSibling);
	let a = i.querySelector("button");
	nn.set(a, Y(a, "影院模式", "T")), rn(a), a.onclick = (e) => {
		e.stopPropagation(), an(!W().settings().theaterMode);
	};
}
function ln(e) {
	let t = e.getChild("controlBar")?.el();
	if (!t || t.querySelector(".vjs-peach-right-controls")) return;
	let n = t.querySelector(":scope>.vjs-play-control");
	n && !n.querySelector(":scope>.vjs-peach-hover") && n.insertAdjacentHTML("beforeend", "<span class=\"vjs-peach-hover\" aria-hidden=\"true\"></span>");
	let r = (e, t) => e ? (e.dataset.peachExplicitIcon = "", e.insertAdjacentHTML("beforeend", f(t, "vjs-peach-control-icon")), e.querySelector(":scope>.vjs-peach-control-icon use")) : null, i = (e, t) => {
		if (!e) return null;
		let n = document.getElementById(`i-${t}`);
		if (!n) return null;
		e.dataset.peachExplicitIcon = "";
		let r = document.createElementNS("http://www.w3.org/2000/svg", "svg");
		return r.setAttribute("viewBox", n.getAttribute("viewBox") || ""), r.setAttribute("aria-hidden", "true"), r.setAttribute("class", "vjs-peach-control-icon vjs-peach-morph-icon"), r.innerHTML = n.innerHTML, e.append(r), r;
	}, a = (e) => [...document.getElementById(`i-${e}`)?.querySelectorAll("path") || []], o = i(n, "player-play")?.querySelector("path"), s = a("player-play")[0]?.getAttribute("d") || "", c = a("player-pause")[0]?.getAttribute("d") || "", l = Y(n, "播放", "K"), d = CSS.supports("d", "path(\"M0 0\")"), p = () => {
		let t = e.paused() || e.ended(), n = t ? s : c;
		o && (d ? o.style.setProperty("d", `path("${n}")`) : o.setAttribute("d", n)), l(t ? "播放" : "暂停");
	};
	e.on([
		"play",
		"pause",
		"ended"
	], p), p();
	let m = t.querySelector(":scope>.vjs-volume-panel"), h = m?.querySelector(":scope>.vjs-mute-control"), g = i(h, "player-volume");
	g && a("player-volume-muted").forEach((e) => g.append(e.cloneNode(!0)));
	let _ = Y(h, "静音", "M"), v = () => {
		let t = e.muted() || e.volume() === 0;
		g && (g.dataset.silent = String(t), g.dataset.loud = String(!t && e.volume() > .5)), _(t ? "取消静音" : "静音");
	};
	e.on("volumechange", v), v();
	let y = document.createElement("div");
	y.className = "vjs-peach-bezel", y.setAttribute("role", "status"), y.hidden = !0, y.innerHTML = `<span class="vjs-peach-bezel-icon">${f("player-play")}</span>`;
	let b = y.querySelector("use"), x = null, S = (e, t) => {
		b?.setAttribute("href", `#i-${e}`), y.setAttribute("aria-label", t), y.hidden = !1, y.classList.remove("vjs-peach-bezel-run"), y.offsetWidth, y.classList.add("vjs-peach-bezel-run"), x && clearTimeout(x), x = setTimeout(() => {
			y.hidden = !0, y.classList.remove("vjs-peach-bezel-run");
		}, 1e3);
	};
	e.el().insertBefore(y, t), e.el().addEventListener("click", (t) => {
		let n = t.target;
		if (n.closest(".vjs-mute-control")) {
			let t = e.muted() || e.volume() === 0;
			S(t ? "player-volume" : "player-volume-muted", t ? "取消静音" : "静音");
		} else if (n.closest(".vjs-play-control,.vjs-tech,.vjs-poster")) {
			let t = e.paused() || e.ended();
			S(t ? "player-play" : "player-pause", t ? "播放" : "暂停");
		}
	}, !0), e.on("dispose", () => {
		x && clearTimeout(x);
	});
	let C = document.createElement("button"), w = !1;
	C.type = "button", C.className = "vjs-peach-time vjs-control", C.dataset.playerTime = "", C.innerHTML = "<span class=\"vjs-peach-time-text\"></span>";
	let T = C.querySelector(".vjs-peach-time-text"), E = Y(C, "显示剩余时间"), D = () => {
		let t = Math.max(0, Number(e.currentTime()) || 0), n = Math.max(0, Number(e.duration()) || 0), r = u(Math.max(0, n - t));
		T.textContent = `${w ? `-${r}` : u(t)} / ${u(n)}`, C.dataset.remaining = String(w), E(w ? "显示已播放时间" : "显示剩余时间", w ? `剩余 ${r}，总时长 ${u(n)}；点击显示已播放时间` : `已播放 ${u(t)}，总时长 ${u(n)}；点击显示剩余时间`);
	};
	C.onclick = (e) => {
		e.stopPropagation(), w = !w, D();
	}, e.on([
		"timeupdate",
		"durationchange",
		"loadedmetadata"
	], D), D(), m ? m.insertAdjacentElement("afterend", C) : t.append(C);
	let O = t.querySelector(":scope>.vjs-picture-in-picture-control");
	r(O, "player-pip");
	let k = Y(O, "画中画");
	e.on(["enterpictureinpicture", "leavepictureinpicture"], () => k(document.pictureInPictureElement ? "退出画中画" : "画中画"));
	let A = t.querySelector(":scope>.vjs-fullscreen-control"), j = r(A, "player-fullscreen-enter"), M = Y(A, "全屏", "F"), ee = () => {
		let t = !!e.isFullscreen();
		e.el().toggleAttribute("data-peach-fullscreen", t), j?.setAttribute("href", t ? "#i-player-fullscreen-exit" : "#i-player-fullscreen-enter"), M(t ? "退出全屏" : "全屏"), zt(e);
	};
	e.on([
		"fullscreenchange",
		"enterFullWindow",
		"exitFullWindow"
	], ee), ee();
	let te = [
		O,
		t.querySelector(":scope>.vjs-peach-settings"),
		t.querySelector(":scope>.vjs-peach-theater"),
		A
	].filter((e) => !!e);
	if (!te.length) return;
	let N = document.createElement("div");
	N.className = "vjs-peach-right-controls", N.setAttribute("aria-label", "播放器视图控制"), t.insertBefore(N, te[0]), te.forEach((e) => {
		e.insertAdjacentHTML("beforeend", "<span class=\"vjs-peach-hover\" aria-hidden=\"true\"></span>"), N.append(e);
	});
	let P = document.createElement("div");
	P.className = "vjs-peach-expand vjs-control", P.innerHTML = `<button type="button" data-player-expand aria-expanded="false">${f("player-expand")}</button><span class="vjs-peach-hover" aria-hidden="true"></span>`, N.prepend(P);
	let ne = P.querySelector("button"), re = Y(ne, "展开控件"), ie = (t) => {
		e.el().classList.toggle("vjs-peach-right-expanded", t), ne.setAttribute("aria-expanded", String(t)), re(t ? "收起控件" : "展开控件");
	};
	ne.onclick = (t) => {
		t.stopPropagation(), ie(!e.el().classList.contains("vjs-peach-right-expanded"));
	};
	let ae = () => {
		let t = e.el(), n = t.clientWidth < 528;
		t.style.setProperty("--peach-player-h", `${t.clientHeight}px`), t.classList.toggle("vjs-peach-xsmall", n), n || ie(!1);
	}, oe = new ResizeObserver(ae);
	oe.observe(e.el()), e.on("dispose", () => oe.disconnect()), ie(!1), ae();
}
function un(e, t, n = {}) {
	let r = e.getChild("controlBar")?.el()?.querySelector(".vjs-progress-control");
	if (!r || r.querySelector("[data-player-seek-preview]")) return;
	let i = n.thumbnail !== !1, a = document.createElement("div");
	a.className = "vjs-peach-seek-preview", a.dataset.playerSeekPreview = "", a.hidden = !0, a.innerHTML = `${i ? "<i class=\"vjs-peach-seek-frame\" hidden><img alt=\"\"></i>" : ""}<span class="mono">0:00</span>`, r.append(a);
	let o = a.querySelector(".vjs-peach-seek-frame"), s = a.querySelector("img"), l = a.querySelector("span"), d = null, f = "";
	o && t.id && c(`/api/timeline?id=${encodeURIComponent(t.id)}`).then((e) => {
		e && e.frames > 0 && e.interval > 0 && (d = e);
	}).catch(() => {});
	let m = (e, n, r, i) => {
		let a = n.columns || 10, o = a * (n.rows || 10), s = Math.min(n.frames - 1, Math.max(0, Math.floor(e / n.interval))), c = Math.floor(s / o), l = s % o, u = Math.ceil(Math.min(o, n.frames - c * o) / a), d = `/timeline?id=${encodeURIComponent(t.id)}&s=${c}`;
		d !== f && (f = d, i.src = d), r.hidden = !1, t.width && t.height && (r.style.aspectRatio = `${t.width} / ${t.height}`), i.style.objectFit = "fill", i.style.width = `${a * 100}%`, i.style.height = `${u * 100}%`, i.style.left = `${-(l % a) * 100}%`, i.style.top = `${-Math.floor(l / a) * 100}%`;
	}, h = -1, g = (n) => {
		if (n.pointerType === "touch") return;
		let i = p(e.duration()) || p(t.duration);
		if (!i) return;
		let c = r.getBoundingClientRect(), f = Math.min(1, Math.max(0, (n.clientX - c.left) / c.width)), g = o ? Math.min(240, Math.max(160, c.width * .28)) : 76, _ = Math.min(c.width - g / 2, Math.max(g / 2, n.clientX - c.left));
		if (a.style.left = `${_}px`, a.hidden = !1, l.textContent = u(i * f), !o || !s) return;
		if (d) {
			m(i * f, d, o, s);
			return;
		}
		let v = Math.min(8, Math.floor(f * 9));
		v !== h && (h = v, o.hidden = !1, s.removeAttribute("style"), s.src = `/poster?id=${encodeURIComponent(t.id)}&c=${v}`);
	}, _ = () => {
		a.hidden = !0;
	};
	s && o && (s.onerror = () => {
		o.hidden = !0;
	}), r.addEventListener("pointermove", g), r.addEventListener("pointerleave", _), e.on("dispose", () => {
		r.removeEventListener("pointermove", g), r.removeEventListener("pointerleave", _);
	});
}
function dn(e, t) {
	let n = navigator.mediaSession;
	if (!n || typeof n.setActionHandler != "function") return;
	let r = () => p(e.duration()) || p(t.duration) || 0, i = (t) => {
		let n = r();
		e.currentTime(Math.max(0, n ? Math.min(n, t) : t));
	}, a = () => Math.max(1, Number(W().settings().seekSeconds) || 10), o = [
		["play", () => {
			e.play();
		}],
		["pause", () => e.pause()],
		["seekbackward", (t) => i(e.currentTime() - (t?.seekOffset || a()))],
		["seekforward", (t) => i(e.currentTime() + (t?.seekOffset || a()))],
		["seekto", (e) => {
			typeof e?.seekTime == "number" && i(e.seekTime);
		}]
	], s = [];
	for (let [e, t] of o) try {
		n.setActionHandler(e, t), s.push(e);
	} catch {}
	let c = () => {
		let t = r(), i = Math.max(0, Number(e.currentTime()) || 0);
		if (typeof n.setPositionState == "function" && !(!t || i > t)) try {
			n.setPositionState({
				duration: t,
				position: i,
				playbackRate: Math.max(.001, Number(e.playbackRate()) || 1)
			});
		} catch {}
	};
	e.on([
		"timeupdate",
		"durationchange",
		"ratechange",
		"seeked",
		"loadedmetadata"
	], c), c(), e.on("dispose", () => {
		s.forEach((e) => {
			try {
				n.setActionHandler(e, null);
			} catch {}
		});
		try {
			n.setPositionState?.();
		} catch {}
	});
}
function fn(e) {
	let t = e.el().querySelector(".vjs-loading-spinner");
	!t || t.querySelector(".vjs-peach-spinner-container") || (t.innerHTML = "<span class=\"vjs-peach-spinner-container\"><span class=\"vjs-peach-spinner-rotator\"><span class=\"vjs-peach-spinner-left\"><span class=\"vjs-peach-spinner-circle\"></span></span><span class=\"vjs-peach-spinner-right\"><span class=\"vjs-peach-spinner-circle\"></span></span></span></span>");
}
function pn(e, t) {
	c(`/api/assets/${t}/subtitles`).then((t) => {
		!e || e.isDisposed() || (t?.subtitles || []).filter((e) => e.playable).forEach((t) => {
			e.addRemoteTextTrack({
				kind: "subtitles",
				src: t.src,
				srclang: t.language || "",
				label: t.label,
				default: !1
			}, !0);
		});
	}).catch(() => {});
}
//#endregion
//#region src/player/stream.ts
function mn() {
	return globalThis.crypto?.randomUUID?.() || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}
function hn(e, t) {
	return {
		src: `/stream?id=${e.id}&session=${encodeURIComponent(t)}`,
		type: String(e.name || "").toLowerCase().endsWith(".webm") ? "video/webm" : "video/mp4"
	};
}
function gn(e) {
	return e.location === "online" && e.follow_item_id ? {
		src: `/follow-stream?id=${e.follow_item_id}`,
		type: "video/mp4"
	} : null;
}
async function _n(e, t) {
	let n = gn(e);
	if (n) return n;
	try {
		let n = await c(`/api/stream-plan?id=${e.id}&session=${encodeURIComponent(t)}`);
		if (n?.protocol === "hls" && n.src) return {
			src: n.src,
			type: n.mime_type || "application/vnd.apple.mpegurl"
		};
	} catch {}
	return hn(e, t);
}
function vn(e) {
	e && fetch(`/api/stream-cancel?session=${encodeURIComponent(e)}`, {
		method: "POST",
		credentials: "same-origin",
		keepalive: !0
	}).then((e) => e.json()).then((e) => {
		document.documentElement.dataset.peachStreamCancel = JSON.stringify(e);
	}).catch(() => {});
}
var X = "";
function yn() {
	return X;
}
function bn() {
	return X ||= mn(), X;
}
var xn = (e) => hn(e, bn()), Sn = (e) => _n(e, bn());
function Cn() {
	let e = X;
	e && (X = "", vn(e));
}
//#endregion
//#region src/player/telemetry.ts
function wn(e, t, n = {}) {
	if (!t) return;
	let r = 0, i = 0, a = 0, o = null;
	t.addEventListener("seeking", () => {
		a++;
	});
	let s = (e) => e ? document.querySelector(e) : null, l = () => {
		let r = p(e.duration) || p(t.duration);
		if (!r) return;
		let i = Math.min(t.currentTime / r, 1), a = s(n.watched), o = s(n.mark), c = s(n.ratio);
		a && (a.style.width = `${(i * 100).toFixed(1)}%`), o && (o.style.left = `${(i * 100).toFixed(1)}%`), c && (c.textContent = `${(i * 100).toFixed(0)}%`);
	}, u = (n) => {
		let r = p(e.duration) || p(t.duration);
		!i && !n && !a || (c("/api/activity", {
			method: "POST",
			body: JSON.stringify({
				id: e.id,
				position: t.currentTime,
				duration: r,
				delta: i,
				ended: !!n,
				seeks: a
			})
		}).then((e) => {
			let t = document.getElementById("realTxt");
			if (t && e && e.real_ratio != null) {
				let n = Math.min(e.real_ratio, 1) * 100;
				t.textContent = `${n.toFixed(0)}%`;
				let r = document.getElementById("realBar");
				r && (r.style.width = `${n.toFixed(1)}%`);
			}
		}).catch(() => {}), i = 0, a = 0);
	}, d = () => {
		o &&= (clearInterval(o), null);
	};
	t.onplay = () => {
		r = t.currentTime, d(), o = setInterval(() => u(!1), 1e4);
	}, t.ontimeupdate = () => {
		let e = t.currentTime - r;
		e > 0 && e < 2 && (i += e), r = t.currentTime, l();
	}, t.onpause = () => {
		d(), u(!1);
	}, t.onended = () => {
		d(), u(!0), n.onEnded?.();
	}, t.addEventListener("emptied", () => {
		d(), u(!1);
	}, { once: !0 }), n.register?.(d), l();
}
function Tn(e, t) {
	let n = 0, r = 0, i = !1, a = null, o = (n) => {
		let i = p(e.duration) || p(t.duration);
		!r && !n || (c("/api/follow/activity", {
			method: "POST",
			body: JSON.stringify({
				item: e.id,
				position: t.currentTime,
				duration: i,
				delta: r,
				ended: !!n
			})
		}).catch(() => {}), r = 0);
	}, s = () => {
		a && clearInterval(a), a = null;
	};
	t.addEventListener("play", () => {
		i || (i = !0, c("/api/follow/play", {
			method: "POST",
			body: JSON.stringify({ item: e.id })
		}).then((t) => {
			e.status = t?.status || e.status;
		}).catch(() => {})), n = t.currentTime, s(), a = setInterval(() => o(!1), 1e4);
	}), t.addEventListener("timeupdate", () => {
		let e = t.currentTime - n;
		e > 0 && e < 2 && (r += e), n = t.currentTime;
	}), t.addEventListener("pause", () => {
		s(), o(!1);
	}), t.addEventListener("ended", () => {
		s(), o(!0);
	}), t.addEventListener("emptied", () => {
		s(), o(!1);
	}, { once: !0 });
}
//#endregion
//#region src/player/videojs.ts
var En = "/vendor/videojs/8.24.1/", Dn = (e) => new Promise((t, n) => {
	let r = document.head.querySelector(`script[src="${e}"]`);
	if (r?.dataset.loaded) {
		t();
		return;
	}
	let i = r ?? document.createElement("script");
	i.addEventListener("load", () => {
		i.dataset.loaded = "1", t();
	}, { once: !0 }), i.addEventListener("error", () => {
		i.remove(), n(/* @__PURE__ */ Error(`script unavailable: ${e}`));
	}, { once: !0 }), r || (i.src = e, document.head.appendChild(i));
}), On = () => globalThis.videojs, kn = null;
function An() {
	let e = On();
	return e ? Promise.resolve(e) : (kn ??= Dn(`${En}video.min.js`).then(() => Dn(`${En}lang/zh-CN.js`)).then(() => {
		let e = On();
		if (!e) throw Error("videojs unavailable");
		return e;
	}).catch((e) => {
		throw kn = null, e;
	}), kn);
}
//#endregion
//#region src/player/detail-player.ts
var Z = null, Q = null, jn = null;
function Mn() {
	Z &&= (clearInterval(Z), null), Q &&= (clearInterval(Q), null), jn &&= (clearTimeout(jn), null);
}
async function Nn(e, t, n, r = {}) {
	let i = q();
	if (i) return i;
	let a = W(), o = r.resume ?? null;
	o?.autoplay && (n = !0);
	let s = document.getElementById("playerStatsBtn"), c = document.getElementById("playerStats"), m = () => r.source ? Promise.resolve(r.source) : Sn(e), h;
	try {
		h = await An();
	} catch {
		return t.controls = !0, m().then((e) => {
			t.src = e.src, n && t.play().catch(() => {});
		}).catch(() => {}), null;
	}
	let g = h(t, {
		controls: !0,
		preload: "metadata",
		language: "zh-CN",
		responsive: !0,
		poster: r.poster || a.posterUrl(e),
		controlBar: {
			pictureInPictureToggle: !0,
			currentTimeDisplay: !0,
			timeDivider: !0,
			durationDisplay: !0,
			remainingTimeDisplay: !1
		}
	});
	Rt(g), g.peachItem = e, It(g), g.on("loadedmetadata", () => {
		let e = g.el()?.querySelector("video");
		e?.videoWidth && e.videoHeight && g.el().style.setProperty("--peach-video-ratio", `${e.videoWidth}/${e.videoHeight}`);
	});
	let _ = p(e.duration), v = {
		speed: [],
		activity: [],
		buffer: []
	}, y = Number(r.size ?? e.size) || 0, b = Wt(Ut(y, e.duration)), x = 0, S = !1, C = () => q() === g && !g.isDisposed(), w = () => {
		if (!_ || S || !C()) return;
		let e = Number(g.duration());
		(!Number.isFinite(e) || Math.abs(e - _) > Math.max(2, _ * .001)) && (S = !0, g.duration(_), queueMicrotask(() => {
			S = !1;
		}));
	}, T = () => String(g.currentSource()?.type || "").includes("mpegurl"), E = () => {
		if (!c || c.hidden || !C()) return;
		let n = t.getVideoPlaybackQuality ? t.getVideoPlaybackQuality() : null, i = t.getBoundingClientRect(), a = `${t.videoWidth || e.width || "?"}×${t.videoHeight || e.height || "?"}`, o = T(), s = yn(), f = o ? Yt(e.id, s) : [], p = f.reduce((e, t) => e + (t.transferSize || t.encodedBodySize || 0), 0), m = f.reduce((e, t) => e + (t.duration || 0), 0) / 1e3;
		b.sample(t);
		let h = Zt(g, e.id, s, o ? null : b) || (m > 0 ? p * 8 / m : 0), S = o ? p : b.bitrate > 0 ? b.bytes() : b.seconds, w = Math.max(0, S - x);
		x = S;
		let E = Bt(t);
		Kt(v.speed, h), Kt(v.activity, w), Kt(v.buffer, E);
		let D = String(e.name || ""), O = (D.includes(".") ? D.split(".").pop() || "" : o ? "" : String(g.currentSource()?.type || "").split("/").pop() || "").toUpperCase() || "—", k = h ? `${(h / 1e6).toFixed(1)} Mbps` : "—", A = o || b.bitrate > 0, j = o ? [
			"网络活动",
			`${p ? d(p) : "—"} · ${f.length} 请求`,
			`最近一秒网络活动 ${w ? d(w) : "0 B"}`
		] : [
			"已下载",
			A ? `${d(S)}${y > 0 ? ` / ${d(y)}` : ""}` : `${S.toFixed(0)} 秒`,
			A ? `最近一秒下载 ${w ? d(w) : "0 B"}` : `最近一秒下载 ${w.toFixed(1)} 秒`
		], M = [
			["视频 ID / 会话", s && !r.source ? `${e.id} / ${s.slice(0, 8)}` : `${e.id}`],
			["视口 / 帧", `${Math.round(i.width)}×${Math.round(i.height)} / ${n ? `${n.totalVideoFrames - n.droppedVideoFrames} of ${n.totalVideoFrames}` : "—"}`],
			["当前 / 最佳分辨率", `${a} / ${e.width || t.videoWidth || "?"}×${e.height || t.videoHeight || "?"}`],
			["编码 / 传输", `${O} / ${o ? "HLS" : "HTTP Range"}`],
			[
				"连接速度",
				k,
				qt(v.speed, "speed", Math.max(1e7, ...v.speed), `连接速度 ${k === "—" ? "暂无数据" : k}`)
			],
			[
				j[0],
				j[1],
				qt(v.activity, "activity", Math.max(1, ...v.activity), j[2])
			],
			[
				"缓冲健康",
				`${E.toFixed(1)} 秒`,
				qt(v.buffer, "buffer", 30, `当前可连续播放 ${E.toFixed(1)} 秒`)
			],
			["播放时间", `${u(t.currentTime)} / ${u(_ || g.duration())}`],
			["日期", (/* @__PURE__ */ new Date()).toLocaleString()]
		];
		c.innerHTML = `<dl>${M.map(([e, t, n]) => `<dt>${l(e)}</dt><dd${n ? " class=\"playerstatsmetric\"" : ""}>${n || ""}<span>${l(t)}</span></dd>`).join("")}</dl>`;
	};
	g.on([
		"loadstart",
		"loadedmetadata",
		"durationchange",
		"error"
	], w);
	let D = !1, O = !1, k = document.getElementById("playerNet"), A = () => {
		if (!k || g.isDisposed()) return;
		let n = T();
		n || b.sample(t);
		let r = Zt(g, e.id, yn(), n ? null : b), i = n ? Qt(r) : $t(r, Bt(t));
		k.innerHTML = `${f("gauge")}<span class="sr-only">加载速度</span><span>${l(i)}</span>`;
	}, j = () => {
		!k || !k.isConnected || (k.hidden = !1, A(), Q && clearInterval(Q), Q = setInterval(A, 500));
	}, M = () => {
		k && (jn && clearTimeout(jn), jn = setTimeout(() => {
			k.hidden = !0, Q &&= (clearInterval(Q), null);
		}, 1400));
	};
	if (g.on([
		"loadstart",
		"progress",
		"waiting",
		"stalled"
	], j), g.on(["canplay", "playing"], () => {
		A(), M();
	}), g.on("error", () => {
		if (D && !O && !g.isDisposed()) {
			O = !0, D = !1, g.src(xn(e)), n && g.play()?.catch(() => {});
			return;
		}
		r.checkSourceStatus !== !1 && a.loadSourceStatus().then((t) => {
			t[String(e.location)] !== !1 || g.isDisposed() || g.error({
				code: 2,
				message: `脱盘模式 · ${a.offlineReason(String(e.location))}`
			});
		});
	}), g.ready(() => {
		w();
		let n = sn(g, t, e.height, r.qualities ?? null);
		r.mediaPromise?.then((t) => {
			if (!C()) return;
			n?.(t?.qualities?.length ? t.qualities : null);
			let r = Number(t?.size) || 0;
			r > 0 && !y && (y = r, b.bitrate = Ut(r, e.duration));
		}).catch(() => {}), un(g, e, { thumbnail: !r.source }), dn(g, e), fn(g), r.source || pn(g, e.id), s && (s.hidden = !1);
	}), s && c) {
		let e = () => {
			c.hidden || (c.hidden = !0, s.setAttribute("aria-pressed", "false"), Z &&= (clearInterval(Z), null));
		};
		s.onclick = () => {
			if (!c.hidden) {
				e();
				return;
			}
			document.dispatchEvent(new CustomEvent(J, { detail: "stats" })), c.hidden = !1, s.setAttribute("aria-pressed", "true"), E(), Z && clearInterval(Z), Z = setInterval(E, 1e3);
		};
		let t = (t) => {
			t.detail !== "stats" && e();
		};
		document.addEventListener(J, t), g.on("dispose", () => document.removeEventListener(J, t));
	}
	return m().then((e) => {
		C() && (D = String(e.type || "").includes("mpegurl"), g.src(e), w(), setTimeout(w, 0), setTimeout(w, 250), o && o.time > 0 && g.one("loadedmetadata", () => {
			g.isDisposed() || g.currentTime(o.time);
		}), n && g.play()?.catch(() => {}));
	}).catch(() => {}), g;
}
function Pn(e, t) {
	let { kind: n, item: r, media: i = null, register: a, handedOff: o } = t, s = W();
	e.parentElement?.insertAdjacentHTML("afterbegin", "<canvas class=\"ambientcanvas\" width=\"32\" height=\"18\"></canvas>"), e.insertAdjacentHTML("beforebegin", Jt());
	let l = { resume: t.resume ?? null };
	if (n === "follow") l = {
		...l,
		source: {
			src: `/follow-stream?id=${r.id}${i ? `&media=${i.index}` : ""}`,
			type: i?.media_type || r.media_type || "video/mp4"
		},
		checkSourceStatus: !1,
		size: i?.size,
		poster: r.thumb_url,
		mediaPromise: c(`/follow-qualities?id=${encodeURIComponent(r.id)}`).catch(() => null)
	};
	else {
		let t = s.posterUrl(r);
		t && (e.poster = t), e.addEventListener("play", () => {
			let e = s.stage();
			e && !e.dataset.c && (e.dataset.c = "1", c("/api/play", {
				method: "POST",
				body: JSON.stringify({ id: r.id })
			}).catch(() => {}));
		}), wn(r, e, {
			watched: "#watched",
			mark: "#mark",
			ratio: "#ratioTxt",
			...a ? { register: a } : {}
		});
	}
	let u = null, d = !1, f = () => {};
	a?.(() => f());
	let p = () => {
		if (!(!u || o?.(u)) && (q() === u && (Rt(null), Mn()), !u.isDisposed())) try {
			u.pause(), u.dispose();
		} catch {}
	};
	return Nn(r, e, t.autoplay ?? s.settings().detailAutoplay, l).then((t) => {
		if (u = t, d) {
			p();
			return;
		}
		f = on(e), u?.one("dispose", f), e.addEventListener("emptied", f, { once: !0 }), n === "follow" && Tn(r, e);
	}), () => {
		d = !0, p();
	};
}
//#endregion
//#region src/islands.ts
var Fn = {
	"catalog-grid": { react: "catalog-grid" },
	"data-cleanup": { react: "data-cleanup" },
	duplicates: { react: "duplicates" },
	"entity-body": { react: "entity-body" },
	"entity-filter": { react: "entity-filter" },
	"entity-hero": { react: "entity-hero" },
	"follow-detail": { react: "follow-detail" },
	"follow-feed": { react: "follow-feed" },
	"follow-manage": { react: "follow-manage" },
	index: { react: "index" },
	"item-detail": { react: "item-detail" },
	"junk-queue": { react: "junk-queue" },
	"library-processing": { react: "library-processing" },
	playlists: { react: "playlists" },
	scraping: { react: "scraping" },
	"quality-goals": { react: "quality-goals" },
	review: { react: "review" },
	configuration: { react: "configuration" },
	"configuration-summary": { react: "configuration-summary" },
	activity: { react: "activity" },
	stats: { react: "stats" },
	taste: { react: "taste" }
}, In = () => import("/dist/peach-react.js").then(() => void 0), Ln = () => Object.keys(Fn), $ = /* @__PURE__ */ new Map();
async function Rn(e, t, n, r = {}) {
	let i = Fn[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	Hn(t);
	let a = { controller: new AbortController() };
	$.set(t, a);
	let o = (await import("/dist/peach-react.js")).pages[i.react];
	try {
		await o.prefetch(n, a.controller.signal);
	} catch {
		if (a.controller.signal.aborted) return;
	}
	if (!Bn(t, a, r)) return;
	let s = () => {
		t.textContent = "";
		let e = t.ownerDocument.createElement("div");
		e.className = "peach-react", t.append(e);
		let r = o.mount(e, n);
		a.dispose = () => {
			r.unmount(), e.remove();
		}, a.props = n, a.update = (e) => r.update(e);
	};
	r.reveal ? r.reveal(t, s) : s();
}
function zn(e, t) {
	let n = e ? $.get(e) : void 0;
	!n?.update || !n.props || (n.props = {
		...n.props,
		...t
	}, n.update(n.props));
}
function Bn(e, t, n) {
	return $.get(e) === t ? n.isCurrent && !n.isCurrent() ? ($.delete(e), !1) : !0 : !1;
}
var Vn = (e) => !!e && $.has(e);
function Hn(e) {
	for (let t of [...$.keys()]) (t === e || e.contains(t)) && Un(t);
}
function Un(e) {
	let t = $.get(e);
	t && (t.controller.abort(), $.delete(e), t.dispose?.());
}
var Wn = null;
function Gn(e, t, n, r) {
	Wn ??= import("/dist/peach-react.js").then((n) => (n.mountToaster(e, t), n)), Wn.then((e) => e.showToast(n, r));
}
//#endregion
export { an as applyTheaterMode, We as boardPageSkeleton, g as boundedPreference, Cn as cancelDetailStream, vn as cancelStreamSession, Je as catalogEmptyHtml, qe as catalogSuggestions, ae as clampPage, st as cleanupSkeletonHtml, en as clickPlayerControl, K as closePlayerMenu, kt as configurePlayer, At as configurePlayerMenu, q as detailPlayer, Ue as detailSkeletonHtml, hn as directStreamSource, Ke as emptyCatalogLayout, An as ensureVideojs, le as entitySkeletonHtml, se as faceSourceScale, Qt as fmtSpeed, ee as followJobProgress, b as initBoardControls, Vn as islandMounted, Ln as islandNames, wt as javImageKind, j as jobActivityHtml, bt as junkCountSkeletonHtml, dt as junkPath, ut as junkRoute, Nn as mountDetailPlayer, Rn as mountIsland, v as mountNumberSetting, Pn as mountPlayer, ce as nativeImageFit, mn as newStreamSession, Ct as normalizeJavImage, xt as normalizeJavLayout, St as normalizeJavPreferences, ie as pageCount, oe as paginationHtml, Tt as panelFrame, _n as playableStreamSource, m as preferredDirection, In as preloadIslands, Dt as relayoutJavImages, P as selectGroup, te as selectRange, N as selectionSummary, Rt as setDetailPlayer, Gn as showToast, Ye as sidebarHasCatalogContent, E as sidebarSectionHtml, Ze as sidebarTagCounts, Mn as stopPlayerPanels, Xt as streamSpeedBits, y as syncBoardRange, Et as syncJavImages, _ as syncNumberSetting, ne as syncSelectionToolbar, Xe as syncSidebarSurface, k as transitionTheme, Hn as unmountIsland, zn as updateIsland, M as watchJob, D as wireSidebarGroups, wn as wireTelemetry };
