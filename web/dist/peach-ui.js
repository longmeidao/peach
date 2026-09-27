import { emptyStateHtml as e, loadingDotsHtml as t, moveGlidePane as n, noteHtml as r, scrollMovesAnchor as i, wireCollapse as a } from "/js/ui-components.js";
import { esc as o, icon as s } from "/js/core.js";
//#region src/sort-preferences.ts
function c(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/number-setting.ts
var l = {
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
function u(e, t, n, r) {
	return Number.isInteger(e) && e >= t && e <= n ? e : r;
}
function d(e, t, n) {
	let r = e.querySelector("input[type=number]"), i = e.querySelector("[role=switch]"), a = e.querySelector(".board-number-fields");
	r && (r.disabled = n, t !== null && t > 0 && (r.value = String(t))), i && (i.disabled = n, t !== null && (i.checked = t > 0)), a && t !== null && (a.hidden = t === 0);
}
function f(e, t, n, r, i) {
	let a = l[t];
	if (!a) return !1;
	let { min: o, max: s, unit: c, optional: d, fallback: f } = a, p = `peach.number.${t}`, m = u(Number(localStorage.getItem(p)), o, s, r > 0 ? r : f), h = document.createElement("div");
	h.className = "board-optional-number";
	let g = document.createElement("div");
	g.className = "board-number-fields", g.hidden = !!d && r === 0;
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
		x(), m = Number(v.value), localStorage.setItem(p, String(m)), i(v.value);
	};
	if (v.addEventListener("change", S), v.addEventListener("keydown", (e) => {
		e.key === "Enter" && (e.preventDefault(), S());
	}), v.addEventListener("input", () => {
		v.value && v.checkValidity() && x();
	}), d) {
		let e = document.createElement("input");
		e.type = "checkbox", e.className = "ptoggle", e.setAttribute("role", "switch"), e.setAttribute("aria-label", `启用${n}`), e.checked = r > 0, e.onchange = () => {
			x(), g.hidden = !e.checked, e.checked ? (v.value = String(m), S()) : (v.value && v.checkValidity() && (m = Number(v.value)), localStorage.setItem(p, String(m)), i("0"));
		}, h.prepend(e);
	}
	return !0;
}
//#endregion
//#region src/board-controls.ts
function p(e) {
	let t = Number(e.min) || 0, n = Number(e.max) || 100, r = Number(e.value), i = n > t ? Math.max(0, Math.min(100, (r - t) / (n - t) * 100)) : 0;
	e.style.setProperty("--board-range-value", `${i}%`);
	let a = e.closest(".dual-range");
	if (!a) return;
	let o = e.id === "durMax" ? "max" : "min", s = a.querySelector(`[data-range-end="${o}"]`);
	s || (s = document.createElement("output"), s.className = "board-range-tip", s.dataset.rangeEnd = o, s.setAttribute("aria-hidden", "true"), a.append(s)), s.textContent = r >= n && o === "max" ? "不限" : `${r} 分钟`, s.style.left = `${i}%`, s.style.setProperty("--range-tip-shift", "0px");
	let c = a.getBoundingClientRect(), l = s.getBoundingClientRect(), u = l.right > c.right ? c.right - l.right : l.left < c.left ? c.left - l.left : 0;
	u && s.style.setProperty("--range-tip-shift", `${Math.round(u)}px`), a.querySelectorAll(".board-range-tip").forEach((e) => e.toggleAttribute("data-range-active", e === s));
}
function m() {
	let e = (e) => {
		e.querySelectorAll("input[type=range]").forEach(p), v(e), g(e);
	};
	e(document), new MutationObserver((t) => {
		for (let n of t) for (let t of n.addedNodes) t instanceof Element && (t.matches("input[type=range]") && p(t), e(t));
	}).observe(document.body, {
		subtree: !0,
		childList: !0
	}), document.addEventListener("input", (e) => {
		e.target instanceof HTMLInputElement && e.target.type === "range" && p(e.target);
	});
	let t = document.createElement("div");
	t.className = "board-tooltip", t.id = "board-control-tooltip", t.role = "tooltip", t.hidden = !0, document.body.append(t);
	let n = null, r = "", a = null, o, s = () => {
		clearTimeout(o), t.hidden = !0, n && (n.hasAttribute("title") || (n.title = r), a === null ? n.removeAttribute("aria-describedby") : n.setAttribute("aria-describedby", a)), n = null;
	}, c = (e, i) => {
		let c = e instanceof Element ? e.closest("[title]") : null;
		!c || c === n || c.closest(".vjs-control") || !c.title.trim() || (s(), n = c, r = c.title, a = c.getAttribute("aria-describedby"), c.removeAttribute("title"), o = setTimeout(() => {
			if (n !== c || !c.isConnected) return;
			t.textContent = r, t.hidden = !1;
			let e = c.getBoundingClientRect(), i = t.getBoundingClientRect();
			t.style.left = `${Math.max(8, Math.min(innerWidth - i.width - 8, e.left + (e.width - i.width) / 2))}px`, t.style.top = `${e.top >= i.height + 16 ? e.top - i.height - 8 : Math.min(innerHeight - i.height - 8, e.bottom + 8)}px`, c.setAttribute("aria-describedby", [a, t.id].filter(Boolean).join(" "));
		}, i));
	};
	document.addEventListener("pointerover", (e) => c(e.target, 400)), document.addEventListener("pointerout", (e) => {
		n && !n.contains(e.relatedTarget) && s();
	}), document.addEventListener("focusin", (e) => c(e.target, 0)), document.addEventListener("focusout", s), document.addEventListener("keydown", (e) => {
		e.key === "Escape" && s();
	}), document.addEventListener("scroll", (e) => {
		n && i(e, n) && s();
	}, !0), window.addEventListener("resize", s);
}
var h = /* @__PURE__ */ new Map();
function g(e) {
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
			n(i), h.set(t, i);
		}, i = h.get(t);
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
var _ = /* @__PURE__ */ new Map();
function v(e) {
	let t = ".iconswitch,.insightswitch,.follow-workspace-switch", r = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && r.push(e), r.forEach((e) => {
		if (e.hasAttribute("data-board-segments") || e.closest("[data-skeleton]")) return;
		e.dataset.boardSegments = "true";
		let t = document.createElement("span");
		t.className = "board-segment-thumb", t.setAttribute("aria-hidden", "true"), e.prepend(t);
		let r = e.className + (e.getAttribute("aria-label") ?? ""), i = _.get(r) ?? null, a = () => {
			let a = e.querySelector("label:has(input:checked),button[aria-selected=true]");
			if (!a || !a.offsetWidth) return;
			let o = {
				x: a.offsetLeft,
				y: a.offsetTop,
				w: a.offsetWidth,
				h: a.offsetHeight
			};
			n(t, i, o, "x"), i = o, _.set(r, o);
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
var y = (e) => e.replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function b(e, t, n = "", r = "") {
	if (!t) return "";
	let i = `sidebar-group-${encodeURIComponent(e)}`;
	return `<details class="sec${r ? " cat-" + y(r) : ""}" data-sidebar-group="${y(e)}"><summary role="button" class="board-section-toggle"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${y(e)}</span></summary><div class="board-sidebar-body" id="${i}">${t}${n}</div></details>`;
}
function x(e) {
	e.querySelectorAll("[data-sidebar-group]").forEach((e) => {
		if (e.dataset.sidebarWired) return;
		e.dataset.sidebarWired = "true";
		let t = e.querySelector(".board-sidebar-body"), n = `peach.sidebar.group.${e.dataset.sidebarGroup}`, r = null;
		try {
			r = sessionStorage.getItem(n);
		} catch {}
		let i = !!t.querySelector("[aria-pressed=true]");
		e.open = r === null ? i : r === "open";
	}), a(e, "details[data-sidebar-group]", "sidebar-collapse"), e.querySelectorAll(".board-section-toggle").forEach((e) => {
		e.dataset.persistWired || (e.dataset.persistWired = "true", e.addEventListener("click", () => {
			let t = `peach.sidebar.group.${e.closest("[data-sidebar-group]").dataset.sidebarGroup}`;
			try {
				sessionStorage.setItem(t, e.getAttribute("aria-expanded") === "true" ? "open" : "closed");
			} catch {}
		}));
	});
}
var S = !1;
async function ee(e, t) {
	if (S) return;
	if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
		t();
		return;
	}
	let n = e.getBoundingClientRect(), r = n.left + n.width / 2, i = n.top + n.height / 2, a = Math.hypot(Math.max(r, innerWidth - r), Math.max(i, innerHeight - i)) * 2.5, o = document.createElement("style");
	o.textContent = `::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:radial-gradient(circle closest-side,#000 78%,#0006 88%,transparent);mask-repeat:no-repeat;will-change:mask-position,mask-size;animation:peach-theme-reveal 560ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${r}px ${i}px;mask-size:0px 0px}to{mask-position:${r - a / 2}px ${i - a / 2}px;mask-size:${a}px ${a}px}}`, S = !0, document.head.append(o);
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
		delete s.dataset.themeSnapshot, o.remove(), S = !1;
	}
}
//#endregion
//#region src/jobs.ts
function te(e, t, n) {
	if (!Number.isFinite(n) || n <= 0) return "";
	let r = Math.max(0, Math.min(n, Number.isFinite(t) ? t : 0)), i = r / n * 100;
	return `<div class="board-job-progress" role="progressbar" aria-label="${o(e)}" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${r}"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle class="board-job-track" cx="18" cy="18" r="15"/><circle class="board-job-fill" cx="18" cy="18" r="15" pathLength="100" stroke-dasharray="${i} ${100 - i}" transform="rotate(-90 18 18)"/></svg><span>${o(e)}<small>${Math.round(i)}%</small></span></div>`;
}
function C(e, n = 0, r = 0) {
	return r > 0 ? te(e, n, r) : t(e);
}
async function w(e) {
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
function ne(e) {
	let n = e.note || ((e) => r(e, {
		label: "任务状态",
		variant: "error"
	})), i = e.loading || t, a = e.progress || ((e, t, n) => C(n || `已处理 ${e} / ${t}`, e, t)), o = e.container || ((e) => `<section class="followtask" data-geist-fieldset aria-label="任务进度"><div class="geist-fieldset-content">${e}</div></section>`), s = document.createElement("div");
	e.host.hidden = !0, s.dataset.followJob = "", s.setAttribute("aria-live", "polite"), e.host.prepend(s);
	let c = e.storageKey || "peach-follow-job", l = sessionStorage.getItem(c) || void 0, u = !1;
	w({
		read: e.read,
		active: () => !u && e.active() && s.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (t) => {
			let r = t.status === "running";
			if (e.host.hidden = !r, e.busy(r), r) {
				l = t.job_id, l && sessionStorage.setItem(c, l);
				let n = t.current, r = (n?.attempt || 1) > 1 ? ` · 第 ${n?.attempt}/${n?.max_attempts} 次尝试${n?.retry_in ? `，${n.retry_in} 秒后重试` : ""}` : "", u = (t.message || (e.title ? e.title + (t.total ? `：已完成 ${t.checked || 0}/${t.total}` : "") : "") || (t.total ? `${t.older ? "抓取历史" : "检查更新"}：已完成 ${t.checked || 0}/${t.total} 个来源` : "正在准备检查任务…")) + (n ? ` · ${n.label || n.provider || ""}${r}` : ""), d = (t.total || 0) > 0 ? a(t.checked || 0, t.total, u) : i(u);
				s.innerHTML = o(d);
			} else if (l && l === t.job_id) l = void 0, u = !0, e.host.hidden = t.status !== "failed", sessionStorage.removeItem(c), s.innerHTML = t.status === "failed" ? n(t.error || "检查失败") : "", e.complete(t);
			else {
				if (l && t.status === "idle") {
					e.host.hidden = !1, s.innerHTML = n("任务状态已失效，请重新发起任务"), sessionStorage.removeItem(c), u = !0;
					return;
				}
				s.innerHTML = "";
			}
		},
		disconnected: () => {
			e.host.hidden = !1, s.innerHTML = n("暂时无法读取进度，正在重新连接…");
		}
	});
}
//#endregion
//#region src/selection.ts
function re(e, t, n, r, i, a = i || !e.has(r)) {
	let o = n === null ? -1 : t.indexOf(n), s = t.indexOf(r);
	return i && o >= 0 && s >= 0 ? t.slice(Math.min(o, s), Math.max(o, s) + 1).forEach((t) => e.add(t)) : a ? e.add(r) : e.delete(r), r;
}
function ie(e, t) {
	let n = t.filter((t) => e.has(t)).length;
	return {
		count: n,
		all: n > 0 && n === t.length,
		mixed: n > 0 && n < t.length
	};
}
function ae(e, t, n) {
	t.forEach((t) => n ? e.add(t) : e.delete(t));
}
function oe({ count: e, label: t, all: n, summary: r, actions: i, locked: a = !1 }) {
	e && (e.textContent = t), n && (n.checked = r.all, n.indeterminate = r.mixed);
	for (let e of i) e.disabled = !r.count || a;
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
	if (!(e > 0 && t > 0 && n > 0 && r > 0)) return 0;
	let i = e / n, a = t / r;
	return i > 1.001 || a > 1.001 || Math.abs(i - a) > Math.max(i, a) * .01 ? 0 : i;
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
//#region src/follow-sort.ts
var T = [
	["checked", "检查时间"],
	["added", "添加时间"],
	["name", "创作者名称"],
	["sources", "来源数量"],
	["source", "来源名称"],
	["provider", "站点"],
	["status", "状态"]
], me = "checked", he = {
	checked: "desc",
	added: "desc",
	name: "asc",
	sources: "desc",
	source: "asc",
	provider: "asc",
	status: "asc"
}, ge = (e) => T.some(([t]) => t === e);
function _e(e, t) {
	let n = ge(e) ? e : me;
	return {
		sort: n,
		dir: t === "asc" || t === "desc" ? t : he[n]
	};
}
//#endregion
//#region src/island-skeleton.ts
var ve = "inline-flex items-center justify-center gap-0.5 whitespace-nowrap overflow-hidden font-sans", E = {
	medium: "h-9 rounded-2lg p-2 text-body-medium",
	small: "h-8 rounded-lg px-2 py-1.5 text-body-medium"
}, ye = {
	medium: E.medium,
	small: "size-8 rounded-lg p-0 text-body-medium"
}, be = {
	medium: "size-5 shrink-0",
	small: "size-[18px] shrink-0"
}, xe = {
	medium: "inline-flex items-center justify-center px-1 shrink-0",
	small: "inline-flex items-center justify-center px-0.5 shrink-0"
}, Se = {
	primary: "bg-button-primary text-text-white shadow-xs",
	secondary: "bg-background-primary-default text-text-primary border border-border-button-default shadow-xs",
	ghost: "bg-button-ghost-background text-button-ghost-foreground"
}, D = (e, t) => `<svg class="${t}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><use href="#i-${e}"/></svg>`;
function O({ variant: e = "primary", size: t = "medium", glyph: n, label: r, attrs: i = "", compact: a = !1 }) {
	let o = r ? E[t] : ye[t], s = n ? D(n, be[t]) : "", c = r ? `<span class="${xe[t]}"${a ? " data-compact-label" : ""}>${r}</span>` : "";
	return `<button type="button" class="${ve} ${o} ${Se[e]}"${i ? ` ${i}` : ""}>${s}${c}</button>`;
}
var Ce = {
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
function k(e, { size: t = "md", className: n = "", attrs: r = "" } = {}) {
	let i = Ce[t];
	return `<div class="group flex flex-col${n ? ` ${n}` : ""}"><button type="button" aria-haspopup="listbox"${r ? ` ${r}` : ""} class="flex w-full items-center justify-between rounded-2lg border border-border-button-default bg-background-primary-default shadow-xs text-text-primary ${i.box}"><span class="flex min-w-0 items-center truncate ${i.value}">${e}</span>${D("chevron-down", `shrink-0 text-text-secondary ${i.chevron}`)}</button></div>`;
}
//#endregion
//#region src/board-skeleton.ts
var A = (e = "60%") => `<span class="skeleton" style="width:${e}"></span>`, j = () => `${A("80%")}${A("48%")}`, M = (e, t) => e.repeat(t), N = (e, t = "metricstrip") => `<div class="${t}">${e.map((e) => `<div class="tastesummary"><span class="board-stat-label">${e}</span><b class="board-stat-value">${A("45%")}</b><small class="board-stat-footer">${A("60%")}</small></div>`).join("")}</div>`, we = (e, t = "skeleton-tabs") => `<div class="${t}">${e.map((e) => `<span>${e}</span>`).join("")}</div>`, Te = (e, t) => `<div class="${t} skeleton-segments" data-board-segments="true">${e.map((e, t) => `<span${t === 0 ? " class=\"skeleton-segment-selected\"" : ""}>${e}</span>`).join("")}</div>`, P = (e) => `<section class="insightpanel"><header>${e}</header><div class="insightpanelbody skeleton-lines">${M(j(), 3)}</div></section>`, F = "disabled data-skeleton-action", I = (e) => `<span class="skeleton skeleton-text" style="width:${e}"></span>`, L = (e, t, n = !1) => `<span class="skeleton" style="width:${e}px;height:${t}px;flex:none${n ? ";border-radius:50%" : ""}"></span>`, Ee = "min-w-0 bg-background-secondary-default rounded-2xl shadow-card flex flex-col gap-3 px-6 py-5 max-sm:gap-2 max-sm:p-4", De = () => `<div class="inline-grid w-full grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 xl:grid-cols-6">${[
	"关注创作者",
	"启用来源",
	"检查失败",
	"未看更新",
	"JAV 订阅",
	"未看新作"
].map((e) => `<div class="${Ee}"><span class="text-body-medium text-text-secondary">${e}</span><b class="text-title-1-medium tabular-nums text-text-primary">${I("3em")}</b></div>`).join("")}</div>`, Oe = "flex min-h-7 flex-none items-center gap-1.5 rounded-md px-2.5 py-1 text-body-medium whitespace-nowrap text-text-secondary data-selected:bg-background-primary-default data-selected:text-text-primary data-selected:shadow-card dark:data-selected:bg-background-primary-hover", ke = () => `<div class="inline-flex w-max max-w-full items-center gap-0.5 overflow-x-auto overscroll-x-contain rounded-2lg bg-background-tertiary-default p-1">${[
	"关注列表",
	"添加关注",
	"JAV 订阅源",
	"来源和凭证"
].map((e, t) => `<span class="${Oe}"${t === 0 ? " data-selected=\"true\"" : ""}>${e}</span>`).join("")}</div>`, R = (e = "") => `<span class="group inline-flex items-center select-none gap-2"><span class="flex shrink-0 items-center justify-center rounded-sm size-4 border bg-background-primary-default shadow-xs border-border-checkbox-default"></span>${e ? `<span class="text-body-medium text-text-primary">${e}</span>` : ""}</span>`, Ae = ({ table: e, sort: t, dir: n }) => {
	let r = T.find(([e]) => e === t)[1];
	return `<div class="flex flex-wrap items-center gap-2 follow-skeleton-toolbar"><h3 class="mr-auto text-title-2-medium text-text-primary">关注列表</h3><span class="text-body-2-regular text-text-secondary">${I("132px")}</span>${O({
		glyph: "refresh-cw",
		label: "检查全部",
		compact: !0,
		attrs: F
	})}<span data-button-group role="group">${O({
		variant: "ghost",
		glyph: "layout-grid",
		attrs: `aria-pressed="${!e}"`
	})}${O({
		variant: "ghost",
		glyph: "table",
		attrs: `aria-pressed="${e}"`
	})}</span>${k(r)}${O({
		variant: "secondary",
		glyph: n === "asc" ? "arrow-up" : "arrow-down"
	})}${e ? "" : O({
		variant: "secondary",
		glyph: "chevron-up",
		label: "全部收起",
		compact: !0,
		attrs: F
	})}</div>`;
}, z = () => `<span class="flex shrink-0 items-center gap-1">${O({
	variant: "secondary",
	size: "small",
	glyph: "refresh-cw",
	attrs: F
})}${O({
	variant: "secondary",
	size: "small",
	glyph: "trash",
	attrs: F
})}</span>`, je = () => `<div class="flex min-h-16 flex-wrap items-center gap-3 px-2 py-3 follow-skeleton-source">${R()}<span class="flex min-w-0 grow flex-col gap-0.5"><span class="text-body-medium">${I("8em")}</span></span><span class="flex shrink-0 items-center gap-1.5">${L(14, 14)}</span>${L(48, 24)}<span class="shrink-0 text-body-2-regular whitespace-nowrap text-text-secondary">${I("113px")}</span>${z()}</div>`, B = (e) => `<section class="min-w-0 bg-background-primary-default rounded-2xl shadow-card flex flex-col overflow-hidden p-2 follow-skeleton-author"><div class="flex flex-wrap items-center gap-3 px-2 py-2.5" data-follow-author-header data-open>${L(32, 32, !0)}<b class="min-w-0 grow text-body-medium break-words text-text-primary">${I("92px")}</b>${O({
	variant: "secondary",
	size: "small",
	glyph: "refresh-cw",
	attrs: F
})}<span class="flex shrink-0 items-center gap-1">${L(14, 14)}${L(14, 14)}</span>${O({
	variant: "secondary",
	size: "small",
	glyph: "check-check",
	label: "全选",
	attrs: F
})}${O({
	variant: "secondary",
	size: "small",
	glyph: "chevron-up",
	label: "收起",
	attrs: F
})}</div><div data-source-divider>${M(je(), e)}</div></section>`, Me = () => {
	try {
		return Number(JSON.parse(localStorage.getItem("peach.settings.v1") || "{}").followPageSize) || 20;
	} catch {
		return 20;
	}
}, Ne = [
	["select", ""],
	["author", "创作者"],
	["source", "来源"],
	["provider", "站点"],
	["status", "状态"],
	["checked", "上次检查"],
	["actions", ""]
], Pe = {
	name: "author",
	source: "source",
	provider: "provider",
	status: "status",
	checked: "checked"
}, Fe = "<svg viewBox=\"0 0 24 24\" fill=\"none\" aria-hidden=\"true\"><path d=\"M12.7071 15.2929C12.3166 15.6834 11.6834 15.6834 11.2929 15.2929L7.70711 11.7071C7.07714 11.0771 7.52331 10 8.41421 10H15.5858C16.4767 10 16.9229 11.0771 16.2929 11.7071L12.7071 15.2929Z\" fill=\"currentColor\"/></svg>", Ie = (e, { sort: t, dir: n }) => `<div data-board-data-table data-follow-table class="follow-skeleton-table"><div class="w-full overflow-x-auto"><table class="bui-table bui-table-sm"><thead><tr>${Ne.map(([e, r]) => r ? `<th><span class="flex items-center gap-0.5">${r}<span data-sort-indicator${Pe[t] === e ? ` data-direction="${n === "asc" ? "ascending" : "descending"}"` : ""}>${Fe}</span></span></th>` : "<th></th>").join("")}</tr></thead><tbody>${M(`<tr>${[
	R(),
	`<span class="flex min-w-0 items-center gap-2">${L(32, 32, !0)}${I("5em")}</span>`,
	I("10em"),
	`<span class="flex items-center gap-1.5">${L(14, 14)}${I("4em")}</span>`,
	L(48, 24),
	I("113px"),
	z()
].map((e) => `<td>${e}</td>`).join("")}</tr>`, e)}</tbody></table></div></div>`, Le = (e, t) => `<div class="flex flex-wrap items-center justify-between gap-3"><span class="text-body-2-regular text-text-secondary">${I("111px")}</span>${k(`每页 ${t} ${e ? "条" : "位"}`, { size: "sm" })}${L(204, 32)}</div>`, Re = (e) => {
	let t = e.followLayout === "table", n = _e(e.followSort, e.followDir), r = e.followPageSize || Me(), i = t ? Ie(r, n) : `${R("全选本页")}<div class="flex flex-col gap-3">${B(3)}${B(4)}${B(3)}</div>`;
	return `<div class="peach-react"><div class="mx-auto flex w-full max-w-board flex-col gap-8">${De()}<div class="flex flex-col gap-6">${ke()}<div class="flex flex-col gap-4"><div class="min-w-0 bg-background-secondary-default rounded-2xl shadow-card flex flex-col gap-4 px-6 py-5 max-sm:px-4 follow-skeleton-surface" data-layout="${t ? "table" : "default"}">${Ae({
		table: t,
		...n
	})}${i}${Le(t, r)}</div></div></div></div></div>`;
};
function ze() {
	return `<div data-skeleton="detail" role="status" aria-label="正在读取作品详情"><div class="sgrid" aria-hidden="true"><div class="vwrap skeleton-detail-media skeleton"></div><aside class="side"><div class="sidecontent skeleton-lines">${A("85%")}${A("65%")}${M(j(), 4)}</div></aside></div></div>`;
}
function Be(e, t = {}) {
	let n = "";
	if (e === "/stats") n = `<div class="insightpage statsdashboard"><header class="insighttoolbar">${A("38%")}</header>${N([
		"馆藏视频",
		"看过",
		"内容标签",
		"使用空间"
	])}${P("馆藏视频")}${P("内容标签")}</div>`;
	else if (e === "/taste") n = `<div class="tastepage"><header class="tastehead">${Te(["浏览器记录", "Peach 内部"], "insightswitch")}${A("24%")}</header><div class="tastestate"></div>${N([
		"浏览记录",
		"口味维度",
		"浏览候选",
		"私有导出"
	], "tastesummaries")}<section class="tastehero"><div class="insightcopy"><span>浏览器画像</span><div class="skeleton skeleton-radar"></div></div><div class="tastebars skeleton-lines">${M(j(), 4)}</div></section>${P("口味分析")}<div class="board-activity-charts">${P("浏览活动")}${P("时间分布")}</div>${P("标签")}</div>`;
	else if (e === "/follow-manage") n = Re(t);
	else if (e === "/configuration") n = `<div class="configpage">${we([
		"通用",
		"媒体",
		"网络与访问",
		"更新与维护"
	])}<section class="configfieldset"><div class="geist-fieldset-content"><h3 class="geist-fieldset-title">开机自启</h3><div class="skeleton-lines">${M(`<div class="skeleton-setting">${A("35%")}<span class="skeleton skeleton-toggle"></span></div>`, 3)}</div></div><footer class="geist-fieldset-footer">${A("100px")}</footer></section></div>`;
	else if (e === "/activity") n = `<div class="activitypage">${[
		"正在进行",
		"被挡下的",
		"最近完成"
	].map((e) => `<section class="activitysection"><h3 class="geist-fieldset-title">${e}</h3><div class="activity-runs"><article class="cleanupfieldset activity-run"><div class="geist-fieldset-content skeleton-lines">${A("35%")}${j()}</div></article></div></section>`).join("")}</div>`;
	else if (e === "/duplicates") n = `<div class="review"><div class="collection-summary">${A("38%")}</div><div class="fsechead dupactions"><h3>批量保留</h3>${A("40%")}</div>${M(`<section class="dupgroup"><div class="duphead">${A("45%")}</div><div class="duplist">${M(`<div class="duprow"><span class="dupcover skeleton"></span><span class="dupmarks">${A()}</span><span class="dupname">${A("90%")}</span>${A()}${A()}${A()}<span class="duppath">${A("70%")}</span></div>`, 2)}</div></section>`, 2)}</div>`;
	else if (e === "/quality-goals") n = `<div class="quality-workspace"><div class="collection-summary"><strong>待升级</strong>${A("20%")}</div><div class="qualitylist">${M(`<article class="qualityitem"><span class="qualitycover skeleton"></span><div class="qualitybody skeleton-lines">${j()}</div><footer class="qualityactions">${A("80%")}</footer></article>`, 6)}</div></div>`;
	else if (e === "/playlists") n = `<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><div class="playlistcreate skeleton-lines"><span>新播放列表</span>${A("200px")}</div></header><div class="playlistcards">${M(`<article class="card playlistcard"><div class="mixstack"><div class="pic skeleton"></div></div><div class="mixmeta"><span class="mav skeleton"></span><div class="mixcopy skeleton-lines">${j()}</div></div></article>`, 6)}</div></section>`;
	else return "";
	return `<div class="board-page-skeleton" data-skeleton="board${e}" role="status" aria-label="正在读取页面"><div aria-hidden="true" inert>${n}</div></div>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var Ve = [
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
function He() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function Ue(e, t) {
	let n = new URLSearchParams();
	for (let t of Ve) e[t] && n.set(t, e[t]);
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
function We({ kind: t = "catalog", filtered: n = !1, jav: r = !1, configurable: i = !1, online: a = !1 } = {}) {
	let o = i ? "<button class=\"geist-button primary\" data-empty-settings>添加内容</button>" : "", s = "<a class=\"geist-button" + (!i || a ? " primary" : "") + "\" href=\"/follow-manage?tab=add\">添加关注</a>";
	if (n || r) return e("search", r ? "还没有符合条件的 JAV 作品" : "没有符合条件的内容", r ? "已扫描但尚未补充发行资料的视频可在全部内容中查看。" : "清除筛选或搜索条件后查看全部内容。", { actions: "<a class=\"geist-button primary\" href=\"/?loc=&thumb=0\">查看全部内容</a>" });
	if (t !== "catalog") {
		let n = (a ? {
			tags: "标签",
			performers: "创作者"
		}[t] : "") || {
			tags: "标签",
			performers: "艺人",
			creators: "创作者",
			studios: "厂牌",
			agencies: "事务所",
			series: "系列"
		}[t] || "资料";
		return e(t === "tags" ? "tags" : "user-round", "还没有" + n, a ? "添加关注来源并获取内容后，这里会显示来源上的" + n + "。" : "添加内容并补充资料后，这里会显示对应信息。", { actions: a ? s : o + s });
	}
	return e("play", "还没有视频", "添加媒体文件夹或关注来源，开始建立你的馆藏。", { actions: o + s });
}
//#endregion
//#region src/sidebar.ts
function Ge(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function Ke(e, t) {
	return e.dataset.surface?.split("?")[0] === t.split("?")[0] && e.querySelector(".dnav") ? (e.dataset.surface = t, !1) : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function qe(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
var Je = "扫描媒体文件夹，导入已有资料，采集缺失信息。两段也可以分开跑：新盘刚接上时先只扫描，几万个文件登记完就能用；采集被网络拖住时只重跑采集，不必再扫一遍磁盘。", Ye = "修缺时间戳表（播放卡顿）和缺索引（打不开）的 MP4。常看的片子先修。", V = "<span class=\"skeleton skeleton-text\" aria-hidden=\"true\"></span>", H = "type=\"button\" disabled data-skeleton-action", U = "disabled data-skeleton-action", Xe = "aria-disabled=\"true\"", W = (e) => `<div class="peach-react"><div class="flex flex-col gap-4">${e}</div></div>`, G = (e, t) => `<div data-geist-fieldset-content>
          <h3 class="text-title-2-medium text-text-primary">${e}</h3>
          <p class="text-body-2-regular text-text-secondary">${t}</p></div>`;
function Ze() {
	return W(`<section aria-label="扫描与采集" data-geist-fieldset data-cleanup-task data-cleanup-processing>
        ${G("扫描与采集", Je)}
        <footer data-geist-fieldset-footer><a href="/scraping" class="inline-flex items-center justify-center gap-1 whitespace-nowrap font-sans rounded-sm text-body-medium text-accent-600"><span>来源和凭证</span>${D("arrow-up", "size-[18px] shrink-0 rotate-90")}</a><span data-button-group data-split-button data-variant="primary">${O({
		glyph: "database",
		label: "扫描并补全资料",
		attrs: U
	})}${O({
		glyph: "chevron-down",
		attrs: `${U} aria-label="更多扫描与采集方式"`
	})}</span></footer>
      </section>`);
}
function Qe() {
	return W(`<section aria-label="媒体修复" data-geist-fieldset data-cleanup-task data-cleanup-processing>
        ${G("媒体修复", Ye)}
        <footer data-geist-fieldset-footer>${k(V, {
		className: "w-48",
		attrs: Xe
	})}${O({
		label: "开始修复",
		attrs: U
	})}</footer>
      </section>`);
}
function $e() {
	let e = [
		["人工复核", "square-check-big"],
		["高清版", "sparkles"],
		["重复文件", "file-stack"],
		["垃圾文件", "file-archive"],
		["回收站", "trash"]
	], t = `<span class="geist-button organize-preset-skeleton">${V}</span>`.repeat(3), n = (e) => `<div class="organizefield"><span>${e}</span>
            <span class="geist-input organize-input-skeleton">${V}</span></div>`;
	return `<div class="cleanuppage" data-skeleton="cleanup" aria-busy="true" aria-label="正在读取数据管理状态">
    <div class="cleanupstats">${e.map(([e, t]) => `
      <button type="button" class="board-plain-stat" disabled>
        <span class="board-plain-stat-head"><span class="board-stat-tile">${s(t)}</span>${e}</span>
        <strong>${V}</strong><span class="cleanupmeta">${V}</span></button>`).join("")}</div>
    <div class="cleanupgrid">
      <div class="cleanupscraping">${Ze()}</div>
      <div class="cleanupmediarepair">${Qe()}</div>
      <section class="cleanupfieldset cleanuporganize" data-geist-fieldset data-cleanup-task aria-labelledby="cleanup-loading-organize">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-organize">整理</h3>
          <p>按模板给文件改名并归入目录。先预览，确认后执行；执行过的一批可以整批退回。</p>
          <div class="organizefields">
            <div class="organizesource"><span class="gselect"><span class="gselectfield organize-source-skeleton">${V}${s("chevron-down")}</span></span></div>
            ${n("文件名模板")}
            ${n("目录模板")}
            <div class="organizepresets">${t}</div>
            <p class="cleanupmeta">${V}</p>
          </div></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button class="geist-button primary" ${H}>预览</button></footer>
      </section></div>
    <section class="resourcesync" aria-labelledby="cleanup-loading-links">
      <h2 id="cleanup-loading-links">链接管理</h2>
      <div class="resourcesyncbox" data-geist-fieldset data-cleanup-task>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">站外链接</h3>
          <div class="linksummary"><div class="linkstats"><div><span>链接总数</span><b>${V}</b><small>${V}</small></div>${[
		"官网/事务所",
		"社交账号",
		"作品资料站"
	].map((e) => `<div><span>${e}</span><b>${V}</b></div>`).join("")}</div>
          <div class="linkhosts"><span>主要站点</span><b>${V}</b></div></div></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" ${H}>${s("unlink")}<span>检查死链</span></button></div>
      </div></section>
    <section class="resourcesync" aria-labelledby="cleanup-loading-sync">
      <h2 id="cleanup-loading-sync">资源同步</h2>
      <div class="resourcesyncbox" data-geist-fieldset data-cleanup-task>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">文件与记录核对</h3>
          <p>按馆藏记录逐条查找本地磁盘与网盘上的文件，列出文件已不存在的记录、空文件夹，以及不再被引用的缓存。</p></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" ${H}>${s("git-compare")}<span>检查文件</span></button></div>
      </div></section></div>`;
}
//#endregion
//#region src/junk-queue.ts
var K = [
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
], et = (e) => K.find(([t]) => t === e)?.[0] ?? "";
function tt(e) {
	let t = new URLSearchParams(e);
	return {
		kind: et(t.get("type")),
		view: t.get("view") === "dismissed" ? "dismissed" : "pending"
	};
}
function q(e = "", t = "pending") {
	let n = new URLSearchParams();
	e && n.set("type", e), t === "dismissed" && n.set("view", "dismissed");
	let r = n.toString();
	return `/junk-files${r ? `?${r}` : ""}`;
}
function nt(e) {
	return e === "dismissed" ? {
		view: "pending",
		label: "返回待判断",
		glyph: "rotate-ccw",
		href: q("", "pending")
	} : {
		view: "dismissed",
		label: "已排除",
		glyph: "eye-off",
		href: q("", "dismissed")
	};
}
var rt = (e) => e === "dismissed" ? "已排除" : "待判断", it = "flex items-end justify-between gap-4 rounded-surface bg-background-secondary-default px-6 py-5 max-compact:flex-col max-compact:items-start max-compact:gap-3 max-compact:p-4 dark:bg-background-primary-default", at = "flex min-w-0 flex-col gap-2", ot = "text-body-regular text-text-secondary", st = "text-display-4-medium tabular-nums text-text-primary", ct = "relative inline-block h-8 w-24 rounded-2lg align-middle skeleton-sheen", J = (e) => `<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-${e}"></use></svg>`;
function lt({ kind: e, view: t }) {
	let n = K.map(([n, r, i]) => `<a href="${q(n, t)}" data-junk-kind-link="${n}"${n === e ? " aria-current=\"page\"" : ""}>${J(i)}${o(r)}</a>`).join(""), r = nt(t);
	return `<div class="peach-react" data-junk-count-skeleton=""><div data-junk-count=""><div data-junk-summary="" aria-live="polite"><div data-collection-summary="" class="${it}"><div class="${at}"><span class="${ot}">${rt(t)}</span><strong class="${st}"><span data-skeleton="count" aria-hidden="true" class="${ct}"></span></strong></div></div></div><div data-junk-filters-frame=""><nav data-junk-filters="" aria-label="垃圾文件分类">${n}<i data-junk-divider="" aria-hidden="true"></i><a href="${r.href}" data-junk-view-link="${r.view}"${t === "dismissed" ? " aria-current=\"page\"" : ""}>${J(r.glyph)}${r.label}</a></nav></div></div></div>`;
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
function ut(e) {
	return {
		javLayout: Y(e.javLayout),
		javImage: X(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function X(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function dt(e, t) {
	return e.is_jav && e.code && e.has_cover && (X(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function ft(e, t) {
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
function pt(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (X(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.classList.remove("panel"), e.removeAttribute("style"), e.closest(".pic,[data-media-pic]")?.style.removeProperty("--cover-blur"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
function mt(e, t) {
	let n = [];
	return e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		e.dataset.javImageLayout !== t && (e.dataset.javImageLayout = t, e.classList.contains("cover") && (e.classList.toggle("whole", t !== "big"), e.classList.toggle("front", t === "big"), e.classList.remove("panel"), e.removeAttribute("style"), e.closest(".pic,[data-media-pic]")?.style.removeProperty("--cover-blur"), e.complete && e.naturalWidth && n.push(e)));
	}), n;
}
//#endregion
//#region src/islands.ts
var Z = {
	"catalog-grid": { react: "catalog-grid" },
	"cover-crop": { react: "cover-crop" },
	"data-cleanup": { react: "data-cleanup" },
	duplicates: { react: "duplicates" },
	"entity-body": { react: "entity-body" },
	"entity-filter": { react: "entity-filter" },
	"entity-hero": { react: "entity-hero" },
	"follow-manage": { react: "follow-manage" },
	index: { react: "index" },
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
}, ht = () => import("/dist/peach-react.js").then(() => void 0), gt = () => Object.keys(Z), Q = /* @__PURE__ */ new Map();
async function _t(e, t, n, r = {}) {
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
	if (!yt(t, a, r)) return;
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
function vt(e, t) {
	let n = e ? Q.get(e) : void 0;
	!n?.update || !n.props || (n.props = {
		...n.props,
		...t
	}, n.update(n.props));
}
function yt(e, t, n) {
	return Q.get(e) === t ? n.isCurrent && !n.isCurrent() ? (Q.delete(e), !1) : !0 : !1;
}
var bt = (e) => !!e && Q.has(e);
function $(e) {
	for (let t of [...Q.keys()]) (t === e || e.contains(t)) && xt(t);
}
function xt(e) {
	let t = Q.get(e);
	t && (t.controller.abort(), Q.delete(e), t.dispose?.());
}
var St = null;
function Ct(e, t, n, r) {
	St ??= import("/dist/peach-react.js").then((n) => (n.mountToaster(e, t), n)), St.then((e) => e.showToast(n, r));
}
//#endregion
export { Be as boardPageSkeleton, u as boundedPreference, We as catalogEmptyHtml, Ue as catalogSuggestions, le as clampPage, $e as cleanupSkeletonHtml, ze as detailSkeletonHtml, He as emptyCatalogLayout, pe as entitySkeletonHtml, de as faceSourceScale, ne as followJobProgress, m as initBoardControls, bt as islandMounted, gt as islandNames, dt as javImageKind, C as jobActivityHtml, lt as junkCountSkeletonHtml, q as junkPath, tt as junkRoute, _t as mountIsland, f as mountNumberSetting, fe as nativeImageFit, X as normalizeJavImage, Y as normalizeJavLayout, ut as normalizeJavPreferences, ce as pageCount, ue as paginationHtml, ft as panelFrame, c as preferredDirection, ht as preloadIslands, mt as relayoutJavImages, ae as selectGroup, re as selectRange, ie as selectionSummary, Ct as showToast, Ge as sidebarHasCatalogContent, b as sidebarSectionHtml, qe as sidebarTagCounts, p as syncBoardRange, pt as syncJavImages, d as syncNumberSetting, oe as syncSelectionToolbar, Ke as syncSidebarSurface, ee as transitionTheme, $ as unmountIsland, vt as updateIsland, w as watchJob, x as wireSidebarGroups };
