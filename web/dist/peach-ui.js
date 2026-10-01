import { emptyStateHtml as e, loadingDotsHtml as t, moveGlidePane as n, noteHtml as r, scrollMovesAnchor as i, wireCollapse as a } from "/js/ui-components.js";
import { api as o, esc as s, icon as c, realDuration as l } from "/js/core.js";
//#region src/sort-preferences.ts
function u(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/settings-store.ts
function d(e, t) {
	let n = /* @__PURE__ */ new Set(), r = 0, i = () => {
		r += 1, n.forEach((e) => e());
	};
	return {
		value: t,
		version: () => r,
		subscribe(e) {
			return n.add(e), () => {
				n.delete(e);
			};
		},
		save() {
			localStorage.setItem(e, JSON.stringify(t)), i();
		},
		notify: i
	};
}
//#endregion
//#region src/number-setting.ts
function f(e, t, n, r) {
	return Number.isInteger(e) && e >= t && e <= n ? e : r;
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
		e.querySelectorAll("input[type=range]").forEach(p), te(e), ee(e);
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
function ee(e) {
	let t = ".managebar-menu,.board-local-nav:not(.settingscard>.board-local-nav):not([data-section-nav])", n = [...e.querySelectorAll(t)];
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
var g = /* @__PURE__ */ new Map();
function te(e) {
	let t = ".iconswitch,.insightswitch,.follow-workspace-switch", r = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && r.push(e), r.forEach((e) => {
		if (e.hasAttribute("data-board-segments") || e.closest("[data-skeleton]")) return;
		e.dataset.boardSegments = "true";
		let t = document.createElement("span");
		t.className = "board-segment-thumb", t.setAttribute("aria-hidden", "true"), e.prepend(t);
		let r = e.className + (e.getAttribute("aria-label") ?? ""), i = g.get(r) ?? null, a = () => {
			let a = e.querySelector("label:has(input:checked),button[aria-selected=true]");
			if (!a || !a.offsetWidth) return;
			let o = {
				x: a.offsetLeft,
				y: a.offsetTop,
				w: a.offsetWidth,
				h: a.offsetHeight
			};
			n(t, i, o, "x"), i = o, g.set(r, o);
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
var _ = (e) => e.replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function ne(e, t, n = "", r = "") {
	if (!t) return "";
	let i = `sidebar-group-${encodeURIComponent(e)}`;
	return `<details class="sec${r ? " cat-" + _(r) : ""}" data-sidebar-group="${_(e)}"><summary role="button" class="board-section-toggle"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${_(e)}</span></summary><div class="board-sidebar-body" id="${i}">${t}${n}</div></details>`;
}
function re(e) {
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
var v = !1;
async function ie(e, t) {
	if (v) return;
	if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
		t();
		return;
	}
	let n = e.getBoundingClientRect(), r = n.left + n.width / 2, i = n.top + n.height / 2, a = Math.hypot(Math.max(r, innerWidth - r), Math.max(i, innerHeight - i)) * 2.5, o = document.createElement("style");
	o.textContent = `::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:radial-gradient(circle closest-side,#000 78%,#0006 88%,transparent);mask-repeat:no-repeat;will-change:mask-position,mask-size;animation:peach-theme-reveal 560ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${r}px ${i}px;mask-size:0px 0px}to{mask-position:${r - a / 2}px ${i - a / 2}px;mask-size:${a}px ${a}px}}`, v = !0, document.head.append(o);
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
		delete s.dataset.themeSnapshot, o.remove(), v = !1;
	}
}
//#endregion
//#region src/jobs.ts
function ae(e, t, n) {
	if (!Number.isFinite(n) || n <= 0) return "";
	let r = Math.max(0, Math.min(n, Number.isFinite(t) ? t : 0)), i = r / n * 100;
	return `<div class="board-job-progress" role="progressbar" aria-label="${s(e)}" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${r}"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle class="board-job-track" cx="18" cy="18" r="15"/><circle class="board-job-fill" cx="18" cy="18" r="15" pathLength="100" stroke-dasharray="${i} ${100 - i}" transform="rotate(-90 18 18)"/></svg><span>${s(e)}<small>${Math.round(i)}%</small></span></div>`;
}
function y(e, n = 0, r = 0) {
	return r > 0 ? ae(e, n, r) : t(e);
}
async function b(e) {
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
function oe(e) {
	let n = e.note || ((e) => r(e, {
		label: "任务状态",
		variant: "error"
	})), i = e.loading || t, a = e.progress || ((e, t, n) => y(n || `已处理 ${e} / ${t}`, e, t)), o = e.container || ((e) => `<section class="followtask" data-geist-fieldset aria-label="任务进度"><div class="geist-fieldset-content">${e}</div></section>`), s = document.createElement("div");
	e.host.hidden = !0, s.dataset.followJob = "", s.setAttribute("aria-live", "polite"), e.host.prepend(s);
	let c = e.storageKey || "peach-follow-job", l = sessionStorage.getItem(c) || void 0, u = !1;
	b({
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
function se(e, t, n, r, i, a = i || !e.has(r)) {
	let o = n === null ? -1 : t.indexOf(n), s = t.indexOf(r);
	return i && o >= 0 && s >= 0 ? t.slice(Math.min(o, s), Math.max(o, s) + 1).forEach((t) => e.add(t)) : a ? e.add(r) : e.delete(r), r;
}
function ce(e, t) {
	let n = t.filter((t) => e.has(t)).length;
	return {
		count: n,
		all: n > 0 && n === t.length,
		mixed: n > 0 && n < t.length
	};
}
function le(e, t, n) {
	t.forEach((t) => n ? e.add(t) : e.delete(t));
}
function ue({ count: e, label: t, all: n, summary: r, actions: i, locked: a = !1 }) {
	e && (e.textContent = t), n && (n.checked = r.all, n.indeterminate = r.mixed);
	for (let e of i) e.disabled = !r.count || a;
}
function de(e, t, n = 1) {
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
function fe(e, t) {
	return Math.max(1, Math.ceil(e / t));
}
function pe(e, t) {
	return Math.min(Math.max(1, Math.floor(e) || 1), t);
}
function me(e, t, n) {
	if (t <= 1) return "";
	let r = de(e, t).map((t) => t === "…" ? "<li class=\"board-page-dots\" aria-hidden=\"true\">…</li>" : `<li><button type="button" class="board-page" data-page="${t}" aria-label="第 ${t} 页"${t === e ? " aria-current=\"page\"" : ""}>${t}</button></li>`).join("");
	return `<nav class="board-pagination" aria-label="${n}">
    <button type="button" class="geist-button" data-page="${e - 1}"${e <= 1 ? " disabled" : ""}><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-left"></use></svg>上一页</button>
    <ul>${r}</ul>
    <button type="button" class="geist-button" data-page="${e + 1}"${e >= t ? " disabled" : ""}>下一页<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"></use></svg></button>
  </nav>`;
}
//#endregion
//#region src/native-image.ts
function he(e, t, n, r) {
	if (!(e > 0 && t > 0 && n > 0 && r > 0)) return 0;
	let i = e / n, a = t / r;
	return i > 1.001 || a > 1.001 || Math.abs(i - a) > Math.max(i, a) * .01 ? 0 : i;
}
function ge(e, t, n, r, i = 1) {
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
function _e(e, t, n) {
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
var ve = [
	["checked", "检查时间"],
	["added", "添加时间"],
	["name", "创作者名称"],
	["sources", "来源数量"],
	["source", "来源名称"],
	["provider", "站点"],
	["status", "状态"]
], ye = "checked", be = {
	checked: "desc",
	added: "desc",
	name: "asc",
	sources: "desc",
	source: "asc",
	provider: "asc",
	status: "asc"
}, xe = (e) => ve.some(([t]) => t === e);
function Se(e, t) {
	let n = xe(e) ? e : ye;
	return {
		sort: n,
		dir: t === "asc" || t === "desc" ? t : be[n]
	};
}
//#endregion
//#region src/island-skeleton.ts
var Ce = "inline-flex items-center justify-center gap-0.5 whitespace-nowrap overflow-hidden font-sans", x = {
	medium: "h-9 rounded-2lg p-2 text-body-medium",
	small: "h-8 rounded-lg px-2 py-1.5 text-body-medium"
}, we = {
	medium: x.medium,
	small: "size-8 rounded-lg p-0 text-body-medium"
}, Te = {
	medium: "size-5 shrink-0",
	small: "size-[18px] shrink-0"
}, Ee = {
	medium: "inline-flex items-center justify-center px-1 shrink-0",
	small: "inline-flex items-center justify-center px-0.5 shrink-0"
}, De = {
	primary: "bg-button-primary text-text-white shadow-xs",
	secondary: "bg-background-primary-default text-text-primary border border-border-button-default shadow-xs",
	ghost: "bg-button-ghost-background text-button-ghost-foreground"
}, S = (e, t) => `<svg class="${t}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><use href="#i-${e}"/></svg>`;
function C({ variant: e = "primary", size: t = "medium", glyph: n, label: r, attrs: i = "", compact: a = !1 }) {
	let o = r ? x[t] : we[t], s = n ? S(n, Te[t]) : "", c = r ? `<span class="${Ee[t]}"${a ? " data-compact-label" : ""}>${r}</span>` : "";
	return `<button type="button" class="${Ce} ${o} ${De[e]}"${i ? ` ${i}` : ""}>${s}${c}</button>`;
}
var Oe = {
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
function w(e, { size: t = "md", className: n = "", attrs: r = "" } = {}) {
	let i = Oe[t];
	return `<div class="group flex flex-col${n ? ` ${n}` : ""}"><button type="button" aria-haspopup="listbox"${r ? ` ${r}` : ""} class="flex w-full items-center justify-between rounded-2lg border border-border-button-default bg-background-primary-default shadow-xs text-text-primary ${i.box}"><span class="flex min-w-0 items-center truncate ${i.value}">${e}</span>${S("chevron-down", `shrink-0 text-text-secondary ${i.chevron}`)}</button></div>`;
}
//#endregion
//#region src/configuration-copy.ts
var ke = "JavDB 或 MISSAV 无法访问时，可填写能访问的镜像域名，Peach 会保留人物页路径。 资料页只显示已有站点身份记录的入口；JavDB 和 MISSAV 还要求有 JAV 目录站记录。 缺少这些记录的 FC2 创作者不会显示这两个入口。", Ae = "仅填域名；留空使用默认地址", T = (e, t) => `<section aria-label="${e}" class="flex w-full flex-col gap-2"><p class="w-full px-3 text-body-2-medium text-text-secondary">${e}</p><div class="flex w-full flex-col rounded-2xl bg-background-secondary-default pl-3">${t}<div class="-ml-3 flex flex-wrap items-center justify-end gap-3 rounded-b-2xl border-t border-separator-border bg-card-footer px-3 py-3">${C({
	label: "保存配置",
	attrs: "disabled data-skeleton-action"
})}</div></div></section>`, E = (e, t = "") => `<div class="flex min-h-[52px] w-full items-center justify-between gap-4 py-2.5 pr-2.5 border-b border-separator-border last:border-b-0"><div class="flex min-w-0 flex-col"><p class="text-body-regular text-text-primary">${e}</p>${t ? `<p class="text-body-2-regular text-text-secondary">${t}</p>` : ""}</div><span class="skeleton configuration-skeleton-toggle"></span></div>`, D = (e) => `<div class="flex w-full flex-col gap-1"><p class="text-body-medium text-text-primary">${e} 地址</p><span class="skeleton configuration-skeleton-input"></span><p class="pt-px text-caption-1-medium text-text-secondary">${Ae}</p></div>`;
function je() {
	return `<div class="peach-react"><div class="configpage">${`<div class="board-local-nav" data-section-nav data-section-items>${[
		"通用",
		"媒体",
		"网络与访问",
		"更新与维护"
	].map((e, t) => `<button type="button" tabindex="-1" aria-selected="${t === 0}">${e}</button>`).join("")}</div>`}<div class="flex flex-col gap-6">${T("开机自启", `<div class="flex flex-col">${E("开机后启动 Peach")}${E("静默启动", "开机后只显示托盘图标，不打开网页；「开机后启动 Peach」打开时生效。")}${E("在桌面创建快捷方式", "双击图标打开 Peach 网页；卸载时一并移除。")}</div>`)}${T("外部入口", `<div class="flex flex-col gap-4 py-4 pr-3"><p class="text-body-2-regular text-text-secondary">${ke}</p>${D("JavDB")}${D("MISSAV")}</div>`)}</div></div></div>`;
}
//#endregion
//#region src/management-skeletons.ts
var O = "relative overflow-hidden skeleton-sheen bg-background-tertiary-default rounded-lg", k = (e = "60%") => `<span class="${O} inline-block max-w-full align-middle" style="width:${e};height:1em"></span>`, A = "disabled data-skeleton-action", j = "min-w-0 rounded-2-5xl bg-background-secondary-default p-5 flex flex-col gap-4 max-sm:p-4";
function Me() {
	let e = [
		"馆藏视频",
		"看过",
		"内容标签",
		"使用空间"
	].map((e, t) => `
    <div class="min-w-0 rounded-2xl shadow-card flex flex-col overflow-hidden pt-4 text-left ${t === 0 ? "ring-2 ring-border-focus-ring bg-background-primary-default" : "bg-background-secondary-default"}">
      <span class="flex min-w-0 items-center gap-2 px-4 text-body-regular text-text-secondary max-sm:gap-1.5 max-sm:px-3"><i class="${O} size-7 max-sm:size-6"></i>${e}</span>
      <b class="px-4 pt-3 pb-4 text-title-1-medium max-sm:px-3 max-sm:pb-3">${k("4em")}</b>
      <small class="mt-auto block min-h-9.5 bg-card-footer px-4 py-2.5 text-caption-1-regular max-sm:px-3 max-sm:py-2">${k("6em")}</small>
    </div>`).join(""), t = (e) => `<section class="${j}" data-stats-chart>
    <header class="flex flex-wrap items-end justify-between gap-x-4 gap-y-1"><span class="flex min-w-0 flex-col gap-1"><h3 class="text-title-2-medium text-text-primary">${e}</h3><b class="text-display-4-medium">${k("4em")}</b></span><small class="text-caption-1-regular text-text-secondary">个视频</small></header>
    <svg class="h-75 w-full max-sm:h-65 text-background-tertiary-default" viewBox="0 0 200 200" fill="none" stroke="currentColor" stroke-width="12">${[
		76,
		54,
		32
	].map((e) => `<circle cx="100" cy="100" r="${e}"/>`).join("")}</svg>
    <div class="inline-grid w-full grid-cols-3 gap-2 max-sm:grid-cols-2">${Array.from({ length: 3 }, () => `<div class="flex min-w-0 flex-col gap-1 rounded-xl bg-background-tertiary-default p-2.5"><span class="text-caption-1-regular">${k()}</span><b class="text-title-2-medium">${k("3em")}</b><small class="text-caption-1-regular">${k()}</small></div>`).join("")}</div>
  </section>`;
	return `<div class="peach-react"><div class="mx-auto flex w-full max-w-board flex-col gap-8">
    <p class="text-caption-1-regular text-text-secondary">账本当前快照 · ${k("12em")}</p>
    <div class="flex flex-col gap-4"><div class="inline-grid w-full grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4" data-stats-metrics>${e}</div>
      <div class="flex flex-col gap-5"><div class="inline-grid w-full gap-5 md:grid-cols-2">${t("网盘与本地")}${t("媒体库")}</div>
        <div class="inline-grid w-full gap-5 md:grid-cols-2 xl:grid-cols-3">${[
		"时长",
		"画质",
		"文件类型"
	].map((e) => `<section class="${j}"><h3 class="text-title-2-medium">${e}</h3><div class="${O} h-64"></div></section>`).join("")}</div>
      </div>
    </div>
    <section class="rounded-surface bg-background-secondary-default dark:bg-background-primary-default">
      <div class="flex flex-wrap gap-3 px-4 pt-3 text-body-regular">${[
		"内容标签",
		"最近看过",
		"标签来源"
	].map((e) => `<span>${e}</span>`).join("")}</div>
      <div class="flex flex-col gap-3 px-4 pt-3.5 pb-4">${Array.from({ length: 5 }, () => `<div class="${O} h-7"></div>`).join("")}</div>
    </section>
  </div></div>`;
}
function Ne() {
	let e = `<div class="duplicate-row items-center gap-3 border-t border-separator-border px-5 py-4 max-compact:p-4">
    <span class="${O} row-span-2 inline-grid aspect-16/10 w-full rounded-2lg"></span>
    <span class="text-body-regular max-duplicate-narrow:col-start-2 max-duplicate-narrow:-col-end-1">${k("70%")}</span>
    ${Array.from({ length: 3 }, () => `<span class="font-mono text-caption-1-regular leading-5">${k("3em")}</span>`).join("")}
    <span class="col-start-2 -col-end-1 min-w-0 pt-0.5 font-mono text-caption-1-regular leading-5 max-duplicate-narrow:col-span-full">${k("75%")}</span>
  </div>`, t = `<section class="mb-6 overflow-hidden rounded-surface bg-background-secondary-default dark:bg-background-primary-default" data-duplicate-group>
    <div class="flex flex-wrap items-center gap-3 bg-background-tertiary-default p-5 max-compact:p-4 dark:bg-background-secondary-default">
      <b class="text-title-2-medium">${k("5em")}</b><span class="font-mono text-caption-1-regular leading-5">${k("8em")}</span>
      <span class="ml-auto flex flex-wrap gap-2 max-compact:ml-0 max-compact:w-full">${[
		"留最大",
		"留最长",
		"整组回收"
	].map((e) => C({
		variant: "secondary",
		size: "small",
		label: e,
		attrs: A
	})).join("")}</span>
    </div>${e.repeat(2)}</section>`;
	return `<div class="peach-react"><div class="mx-auto w-full max-w-board pb-10.5">
    <div data-collection-summary class="mb-5 flex items-end justify-between gap-4 rounded-surface bg-background-secondary-default px-6 py-5 max-compact:flex-col max-compact:items-start max-compact:gap-3 max-compact:p-4 dark:bg-background-primary-default">
      <div class="flex min-w-0 flex-col gap-2"><span class="text-body-regular text-text-secondary">重复内容</span><strong class="text-display-4-medium">${k("4em")}</strong></div><p class="text-body-regular text-text-secondary">${k("12em")}</p>
    </div>
    <div data-filter-glass data-glass-pane class="mb-5.5 flex flex-wrap items-center gap-x-2.5 gap-y-2 px-4 py-2.5"><h3 class="mr-1 text-body-medium">批量保留</h3>${["全部保留最大", "全部保留最长"].map((e) => `<button ${A} class="h-7.5 rounded-full border border-separator-border px-3 text-body-2-medium">${e}</button>`).join("")}</div>
    ${t.repeat(2)}
  </div></div>`;
}
//#endregion
//#region src/board-skeleton.ts
var M = (e = "60%") => `<span class="skeleton" style="width:${e}"></span>`, N = () => `${M("80%")}${M("48%")}`, P = (e, t) => e.repeat(t), Pe = (e, t = "metricstrip") => `<div class="${t}">${e.map((e) => `<div class="tastesummary"><span class="board-stat-label">${e}</span><b class="board-stat-value">${M("45%")}</b><small class="board-stat-footer">${M("60%")}</small></div>`).join("")}</div>`, Fe = (e, t) => `<div class="${t} skeleton-segments" data-board-segments="true">${e.map((e, t) => `<span${t === 0 ? " class=\"skeleton-segment-selected\"" : ""}>${e}</span>`).join("")}</div>`, F = (e) => `<section class="insightpanel"><header>${e}</header><div class="insightpanelbody skeleton-lines">${P(N(), 3)}</div></section>`, I = "disabled data-skeleton-action", L = (e) => `<span class="skeleton skeleton-text" style="width:${e}"></span>`, R = (e, t, n = !1) => `<span class="skeleton" style="width:${e}px;height:${t}px;flex:none${n ? ";border-radius:50%" : ""}"></span>`, Ie = "min-w-0 bg-background-secondary-default rounded-2xl shadow-card flex flex-col gap-3 px-6 py-5 max-sm:gap-2 max-sm:p-4", Le = () => `<div class="inline-grid w-full grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 xl:grid-cols-6">${[
	"关注创作者",
	"启用来源",
	"检查失败",
	"未看更新",
	"JAV 订阅",
	"未看新作"
].map((e) => `<div class="${Ie}"><span class="text-body-medium text-text-secondary">${e}</span><b class="text-title-1-medium tabular-nums text-text-primary">${L("3em")}</b></div>`).join("")}</div>`, Re = () => `<div data-section-nav data-section-items class="flex max-w-full flex-nowrap overflow-x-auto">${[
	"关注列表",
	"添加关注",
	"JAV 订阅源",
	"来源和凭证"
].map((e, t) => `<span class="whitespace-nowrap" aria-selected="${t === 0}">${e}</span>`).join("")}</div>`, z = (e = "") => `<span class="group inline-flex items-center select-none gap-2"><span class="flex shrink-0 items-center justify-center rounded-sm size-4 border bg-background-primary-default shadow-xs border-border-checkbox-default"></span>${e ? `<span class="text-body-medium text-text-primary">${e}</span>` : ""}</span>`, ze = ({ table: e, sort: t, dir: n }) => {
	let r = ve.find(([e]) => e === t)[1];
	return `<div class="flex flex-wrap items-center gap-2 follow-skeleton-toolbar"><h3 class="mr-auto text-title-2-medium text-text-primary">关注列表</h3><span class="text-body-2-regular text-text-secondary">${L("132px")}</span>${C({
		glyph: "refresh-cw",
		label: "检查全部",
		compact: !0,
		attrs: I
	})}<span data-button-group role="group">${C({
		variant: "ghost",
		glyph: "layout-grid",
		attrs: `aria-pressed="${!e}"`
	})}${C({
		variant: "ghost",
		glyph: "table",
		attrs: `aria-pressed="${e}"`
	})}</span>${w(r)}${C({
		variant: "secondary",
		glyph: n === "asc" ? "arrow-up" : "arrow-down"
	})}${e ? "" : C({
		variant: "secondary",
		glyph: "chevron-up",
		label: "全部收起",
		compact: !0,
		attrs: I
	})}</div>`;
}, B = () => `<span class="flex shrink-0 items-center gap-1">${C({
	variant: "secondary",
	size: "small",
	glyph: "refresh-cw",
	attrs: I
})}${C({
	variant: "secondary",
	size: "small",
	glyph: "trash",
	attrs: I
})}</span>`, Be = () => `<div class="flex min-h-16 flex-wrap items-center gap-3 px-2 py-3 follow-skeleton-source">${z()}<span class="flex min-w-0 grow flex-col gap-0.5"><span class="text-body-medium">${L("8em")}</span></span><span class="flex shrink-0 items-center gap-1.5">${R(14, 14)}</span>${R(48, 24)}<span class="shrink-0 text-body-2-regular whitespace-nowrap text-text-secondary">${L("113px")}</span>${B()}</div>`, V = (e) => `<section class="min-w-0 bg-background-primary-default rounded-2xl shadow-card flex flex-col overflow-hidden p-2 follow-skeleton-author"><div class="flex flex-wrap items-center gap-3 px-2 py-2.5" data-follow-author-header data-open>${R(32, 32, !0)}<b class="min-w-0 grow text-body-medium break-words text-text-primary">${L("92px")}</b>${C({
	variant: "secondary",
	size: "small",
	glyph: "refresh-cw",
	attrs: I
})}<span class="flex shrink-0 items-center gap-1">${R(14, 14)}${R(14, 14)}</span>${C({
	variant: "secondary",
	size: "small",
	glyph: "check-check",
	label: "全选",
	attrs: I
})}${C({
	variant: "secondary",
	size: "small",
	glyph: "chevron-up",
	label: "收起",
	attrs: I
})}</div><div data-source-divider>${P(Be(), e)}</div></section>`, Ve = () => {
	try {
		return Number(JSON.parse(localStorage.getItem("peach.settings.v1") || "{}").followPageSize) || 20;
	} catch {
		return 20;
	}
}, He = [
	["select", ""],
	["author", "创作者"],
	["source", "来源"],
	["provider", "站点"],
	["status", "状态"],
	["checked", "上次检查"],
	["actions", ""]
], Ue = {
	name: "author",
	source: "source",
	provider: "provider",
	status: "status",
	checked: "checked"
}, We = "<svg viewBox=\"0 0 24 24\" fill=\"none\" aria-hidden=\"true\"><path d=\"M12.7071 15.2929C12.3166 15.6834 11.6834 15.6834 11.2929 15.2929L7.70711 11.7071C7.07714 11.0771 7.52331 10 8.41421 10H15.5858C16.4767 10 16.9229 11.0771 16.2929 11.7071L12.7071 15.2929Z\" fill=\"currentColor\"/></svg>", Ge = (e, { sort: t, dir: n }) => `<div data-board-data-table data-follow-table class="follow-skeleton-table"><div class="w-full overflow-x-auto"><table class="bui-table bui-table-sm"><thead><tr>${He.map(([e, r]) => r ? `<th><span class="flex items-center gap-0.5">${r}<span data-sort-indicator${Ue[t] === e ? ` data-direction="${n === "asc" ? "ascending" : "descending"}"` : ""}>${We}</span></span></th>` : "<th></th>").join("")}</tr></thead><tbody>${P(`<tr>${[
	z(),
	`<span class="flex min-w-0 items-center gap-2">${R(32, 32, !0)}${L("5em")}</span>`,
	L("10em"),
	`<span class="flex items-center gap-1.5">${R(14, 14)}${L("4em")}</span>`,
	R(48, 24),
	L("113px"),
	B()
].map((e) => `<td>${e}</td>`).join("")}</tr>`, e)}</tbody></table></div></div>`, Ke = (e, t) => `<div class="flex flex-wrap items-center justify-between gap-3"><span class="text-body-2-regular text-text-secondary">${L("111px")}</span>${w(`每页 ${t} ${e ? "条" : "位"}`, { size: "sm" })}${R(204, 32)}</div>`, qe = (e) => {
	let t = e.followLayout === "table", n = Se(e.followSort, e.followDir), r = e.followPageSize || Ve(), i = t ? Ge(r, n) : `${z("全选本页")}<div class="flex flex-col gap-3">${V(3)}${V(4)}${V(3)}</div>`;
	return `<div class="peach-react"><div class="mx-auto flex w-full max-w-board flex-col gap-8">${Le()}<div class="flex flex-col gap-6">${Re()}<div class="flex flex-col gap-4"><div class="min-w-0 bg-background-secondary-default rounded-2xl shadow-card flex flex-col gap-4 px-6 py-5 max-sm:px-4 follow-skeleton-surface" data-layout="${t ? "table" : "default"}">${ze({
		table: t,
		...n
	})}${i}${Ke(t, r)}</div></div></div></div></div>`;
};
function Je() {
	return `<div data-stage-grid="" aria-hidden="true"><div data-stage-media="" class="skeleton-detail-media skeleton"></div><aside data-stage-side=""><div data-stage-side-content="" class="skeleton-lines">${M("85%")}${M("65%")}${P(N(), 4)}</div></aside></div>`;
}
function Ye() {
	return `<div data-skeleton="detail" role="status" aria-label="正在读取作品详情">${Je()}</div>`;
}
function Xe(e, t = {}) {
	let n = "";
	if (e === "/stats") n = Me();
	else if (e === "/taste") n = `<div class="tastepage"><header class="tastehead">${Fe(["浏览器记录", "Peach 内部"], "insightswitch")}${M("24%")}</header><div class="tastestate"></div>${Pe([
		"浏览记录",
		"口味维度",
		"浏览候选",
		"私有导出"
	], "tastesummaries")}<section class="tastehero"><div class="insightcopy"><span>浏览器画像</span><div class="skeleton skeleton-radar"></div></div><div class="tastebars skeleton-lines">${P(N(), 4)}</div></section>${F("口味分析")}<div class="board-activity-charts">${F("浏览活动")}${F("时间分布")}</div>${F("标签")}</div>`;
	else if (e === "/follow-manage") n = qe(t);
	else if (e === "/configuration") n = je();
	else if (e === "/activity") n = `<div class="activitypage">${[
		"正在进行",
		"被挡下的",
		"最近完成"
	].map((e) => `<section class="activitysection"><h3 class="geist-fieldset-title">${e}</h3><div class="activity-runs"><article class="cleanupfieldset activity-run"><div class="geist-fieldset-content skeleton-lines">${M("35%")}${N()}</div></article></div></section>`).join("")}</div>`;
	else if (e === "/duplicates") n = Ne();
	else if (e === "/quality-goals") n = `<div class="quality-workspace"><div class="collection-summary"><strong>待升级</strong>${M("20%")}</div><div class="qualitylist">${P(`<article class="qualityitem"><span class="qualitycover skeleton"></span><div class="qualitybody skeleton-lines">${N()}</div><footer class="qualityactions">${M("80%")}</footer></article>`, 6)}</div></div>`;
	else if (e === "/playlists") n = `<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><div class="playlistcreate skeleton-lines"><span>新播放列表</span>${M("200px")}</div></header><div class="playlistcards">${P(`<article class="card playlistcard"><div class="mixstack"><div class="pic skeleton"></div></div><div class="mixmeta"><span class="mav skeleton"></span><div class="mixcopy skeleton-lines">${N()}</div></div></article>`, 6)}</div></section>`;
	else return "";
	return `<div class="board-page-skeleton" data-skeleton="board${e}" role="status" aria-label="正在读取页面"><div aria-hidden="true" inert>${n}</div></div>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var Ze = [
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
async function Qe(e, t) {
	let n = new URLSearchParams();
	for (let t of Ze) e[t] && n.set(t, e[t]);
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
function $e({ kind: t = "catalog", filtered: n = !1, jav: r = !1, configurable: i = !1, online: a = !1 } = {}) {
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
//#region src/catalog-filter-skeleton.ts
var et = 64, H = (e) => e.replace(/[&<>"]/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;"
})[e]), tt = (e) => e.repeat(et);
function nt(e, t) {
	let n = e.map((e) => `<a href="${H(e.href)}" data-catalog-view="${H(e.k)}" data-entity-press="" aria-pressed="${t === e.k}">${H(e.label)}</a>`).join("");
	return "<div class=\"peach-react\"><div class=\"contents\" data-catalog-root=\"\" data-loading=\"\"><div data-catalog-tiers=\"\" aria-busy=\"true\"><div data-catalog-tier=\"performers\" data-skeleton=\"tiers\">" + tt("<span data-catalog-placeholder=\"performer\" aria-hidden=\"true\"><span></span><span>&nbsp;</span></span>") + "</div><div data-catalog-tier=\"studios\">" + tt("<span data-catalog-placeholder=\"studio\" aria-hidden=\"true\"><span></span><span>&nbsp;</span></span>") + `</div></div><div role="group" aria-label="筛选与排序" data-filter-glass="" data-glass-pane="" data-filter-frame="" data-catalog-frame="" class="sticky top-topbar z-10 mb-5.5 flex flex-col mx-4"><div role="group" aria-label="视图与标签" data-filter-row="top" class="flex h-12 min-w-0 items-center overscroll-x-contain px-3 py-2 gap-1.5 overflow-visible"><div data-catalog-scroll=""><div role="group" aria-label="视图" data-catalog-views="">${n}<span data-entity-sep="" aria-hidden="true"></span></div><div data-catalog-tags=""><span data-catalog-placeholder="tag" aria-hidden="true">` + "<span></span>".repeat(et) + "</span></div></div></div><div data-filter-row=\"bottom\" aria-busy=\"true\" class=\"flex min-w-0 items-center gap-3 px-3 py-2 min-h-12\"><span data-catalog-readout=\"\"><span data-skeleton=\"count\" aria-hidden=\"true\" class=\"relative inline-block h-3.5 w-37.5 rounded-md align-middle skeleton-sheen\"></span></span></div></div></div></div>";
}
//#endregion
//#region src/sidebar.ts
function rt(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function it(e, t) {
	return e.dataset.surface?.split("?")[0] === t.split("?")[0] && e.querySelector(".dnav") ? (e.dataset.surface = t, !1) : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function at(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
var ot = "扫描媒体文件夹，导入已有资料，采集缺失信息。两段也可以分开跑：新盘刚接上时先只扫描，几万个文件登记完就能用；采集被网络拖住时只重跑采集，不必再扫一遍磁盘。", st = "修缺时间戳表（播放卡顿）和缺索引（打不开）的 MP4。常看的片子先修。", U = "<span class=\"skeleton skeleton-text\" aria-hidden=\"true\"></span>", W = "type=\"button\" disabled data-skeleton-action", G = "disabled data-skeleton-action", ct = "aria-disabled=\"true\"", lt = (e) => `<div class="peach-react"><div class="flex flex-col gap-4">${e}</div></div>`, ut = (e, t) => `<div data-geist-fieldset-content>
          <h3 class="text-title-2-medium text-text-primary">${e}</h3>
          <p class="text-body-2-regular text-text-secondary">${t}</p></div>`;
function dt() {
	return lt(`<section aria-label="扫描与采集" data-geist-fieldset data-cleanup-task data-cleanup-processing data-fieldset-stack>
        ${ut("扫描与采集", ot)}
        <footer data-geist-fieldset-footer><a href="/scraping" class="inline-flex items-center justify-center gap-1 whitespace-nowrap font-sans rounded-sm text-body-medium text-accent-600"><span>来源和凭证</span>${S("arrow-up", "size-[18px] shrink-0 rotate-90")}</a><span data-button-group data-split-button data-variant="primary">${C({
		glyph: "database",
		label: "扫描并补全资料",
		attrs: G
	})}${C({
		glyph: "chevron-down",
		attrs: `${G} aria-label="更多扫描与采集方式"`
	})}</span></footer>
      </section>`);
}
function ft() {
	return lt(`<section aria-label="媒体修复" data-geist-fieldset data-cleanup-task data-cleanup-processing>
        ${ut("媒体修复", st)}
        <footer data-geist-fieldset-footer>${w(U, {
		className: "w-48",
		attrs: ct
	})}${C({
		label: "开始修复",
		attrs: G
	})}</footer>
      </section>`);
}
function pt() {
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
        <span class="board-plain-stat-head"><span class="board-stat-tile">${c(t)}</span>${e}</span>
        <strong>${U}</strong><span class="cleanupmeta">${U}</span></button>`).join("")}</div>
    <div class="cleanupgrid">
      <div class="cleanupscraping">${dt()}</div>
      <div class="cleanupmediarepair">${ft()}</div>
      <section class="cleanupfieldset cleanuporganize" data-geist-fieldset data-cleanup-task aria-labelledby="cleanup-loading-organize">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-organize">整理</h3>
          <p>按模板给文件改名并归入目录。先预览，确认后执行；执行过的一批可以整批退回。</p>
          <div class="organizefields">
            <div class="organizesource"><span class="gselect"><span class="gselectfield organize-source-skeleton">${U}${c("chevron-down")}</span></span></div>
            ${n("文件名模板")}
            ${n("目录模板")}
            <div class="organizepresets">${t}</div>
            <p class="cleanupmeta">${U}</p>
          </div></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button class="geist-button primary" ${W}>预览</button></footer>
      </section></div>
    <section class="resourcesync" aria-labelledby="cleanup-loading-links">
      <h2 id="cleanup-loading-links">链接管理</h2>
      <div class="resourcesyncbox" data-geist-fieldset data-cleanup-task data-fieldset-stack>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">站外链接</h3>
          <div class="linksummary"><div class="linkstats"><div><span>链接总数</span><b>${U}</b><small>${U}</small></div>${[
		"官网/事务所",
		"社交账号",
		"作品资料站"
	].map((e) => `<div><span>${e}</span><b>${U}</b></div>`).join("")}</div>
          <div class="linkhosts"><span>主要站点</span><b>${U}</b></div></div></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" ${W}>${c("unlink")}<span>检查死链</span></button></div>
      </div></section>
    <section class="resourcesync" aria-labelledby="cleanup-loading-sync">
      <h2 id="cleanup-loading-sync">资源同步</h2>
      <div class="resourcesyncbox" data-geist-fieldset data-cleanup-task>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">文件与记录核对</h3>
          <p>按馆藏记录逐条查找本地磁盘与网盘上的文件，列出文件已不存在的记录、空文件夹，以及不再被引用的缓存。</p></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" ${W}>${c("git-compare")}<span>检查文件</span></button></div>
      </div></section></div>`;
}
//#endregion
//#region src/junk-queue.ts
var mt = [
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
], ht = (e) => mt.find(([t]) => t === e)?.[0] ?? "";
function gt(e) {
	let t = new URLSearchParams(e);
	return {
		kind: ht(t.get("type")),
		view: t.get("view") === "dismissed" ? "dismissed" : "pending"
	};
}
function K(e = "", t = "pending") {
	let n = new URLSearchParams();
	e && n.set("type", e), t === "dismissed" && n.set("view", "dismissed");
	let r = n.toString();
	return `/junk-files${r ? `?${r}` : ""}`;
}
function _t(e) {
	return e === "dismissed" ? {
		view: "pending",
		label: "返回待判断",
		glyph: "rotate-ccw",
		href: K("", "pending")
	} : {
		view: "dismissed",
		label: "已排除",
		glyph: "eye-off",
		href: K("", "dismissed")
	};
}
var vt = (e) => e === "dismissed" ? "已排除" : "待判断", yt = "flex items-end justify-between gap-4 rounded-surface bg-background-secondary-default px-6 py-5 max-compact:flex-col max-compact:items-start max-compact:gap-3 max-compact:p-4 dark:bg-background-primary-default", bt = "flex min-w-0 flex-col gap-2", xt = "text-body-regular text-text-secondary", St = "text-display-4-medium tabular-nums text-text-primary", Ct = "relative inline-block h-8 w-24 rounded-2lg align-middle skeleton-sheen", wt = (e) => `<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-${e}"></use></svg>`;
function Tt({ kind: e, view: t }) {
	let n = mt.map(([n, r, i]) => `<a href="${K(n, t)}" data-junk-kind-link="${n}"${n === e ? " aria-current=\"page\"" : ""}>${wt(i)}${s(r)}</a>`).join(""), r = _t(t);
	return `<div class="peach-react" data-junk-count-skeleton=""><div data-junk-count=""><div data-junk-summary="" aria-live="polite"><div data-collection-summary="" class="${yt}"><div class="${bt}"><span class="${xt}">${vt(t)}</span><strong class="${St}"><span data-skeleton="count" aria-hidden="true" class="${Ct}"></span></strong></div></div></div><div data-junk-filters-frame=""><nav data-junk-filters="" aria-label="垃圾文件分类">${n}<i data-junk-divider="" aria-hidden="true"></i><a href="${r.href}" data-junk-view-link="${r.view}"${t === "dismissed" ? " aria-current=\"page\"" : ""}>${wt(r.glyph)}${r.label}</a></nav></div></div></div>`;
}
//#endregion
//#region src/jav-artwork.ts
function Et(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function Dt(e) {
	return {
		javLayout: Et(e.javLayout),
		javImage: q(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function q(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function Ot(e, t) {
	return e.is_jav && e.code && e.has_cover && (q(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function kt(e, t) {
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
function At(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (q(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.classList.remove("panel"), e.removeAttribute("style"), e.closest(".pic,[data-media-pic]")?.style.removeProperty("--cover-blur"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
function jt(e, t) {
	let n = [];
	return e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		e.dataset.javImageLayout !== t && (e.dataset.javImageLayout = t, e.classList.contains("cover") && (e.classList.toggle("whole", t !== "big"), e.classList.toggle("front", t === "big"), e.classList.remove("panel"), e.removeAttribute("style"), e.closest(".pic,[data-media-pic]")?.style.removeProperty("--cover-blur"), e.complete && e.naturalWidth && n.push(e)));
	}), n;
}
//#endregion
//#region src/player/stats.ts
function Mt(e, t = "") {
	let n = t ? encodeURIComponent(t) : "";
	return performance.getEntriesByType("resource").filter((t) => t.name.includes("/stream") && (t.name.includes(`/stream?id=${e}`) || t.name.includes(`/stream/hls/${e}/`)) && (!n || t.name.includes(`session=${n}`)));
}
function Nt(e, t = "") {
	let n = Mt(e, t), r = n.reduce((e, t) => e + (t.transferSize || t.encodedBodySize || 0), 0), i = n.reduce((e, t) => e + (t.duration || 0), 0) / 1e3;
	return r > 0 && i > 0 ? r * 8 / i : 0;
}
function Pt(e) {
	if (!Number.isFinite(e) || e <= 0) return "加载中…";
	let t = e / 8;
	return t >= 1048576 ? `${(t / 1048576).toFixed(1)} MB/s` : `${Math.max(1, Math.round(t / 1024))} KB/s`;
}
//#endregion
//#region src/player/controls.ts
function Ft(e, t) {
	e?.closest(".video-js")?.querySelector(`.vjs-control-bar ${t}`)?.click();
}
//#endregion
//#region src/player/stream.ts
function It() {
	return globalThis.crypto?.randomUUID?.() || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}
function Lt(e, t) {
	return {
		src: `/stream?id=${e.id}&session=${encodeURIComponent(t)}`,
		type: String(e.name || "").toLowerCase().endsWith(".webm") ? "video/webm" : "video/mp4"
	};
}
function Rt(e) {
	return e.location === "online" && e.follow_item_id ? {
		src: `/follow-stream?id=${e.follow_item_id}`,
		type: "video/mp4"
	} : null;
}
async function zt(e, t) {
	let n = Rt(e);
	if (n) return n;
	try {
		let n = await o(`/api/stream-plan?id=${e.id}&session=${encodeURIComponent(t)}`);
		if (n?.protocol === "hls" && n.src) return {
			src: n.src,
			type: n.mime_type || "application/vnd.apple.mpegurl"
		};
	} catch {}
	return Lt(e, t);
}
function Bt(e) {
	e && fetch(`/api/stream-cancel?session=${encodeURIComponent(e)}`, {
		method: "POST",
		credentials: "same-origin",
		keepalive: !0
	}).then((e) => e.json()).then((e) => {
		document.documentElement.dataset.peachStreamCancel = JSON.stringify(e);
	}).catch(() => {});
}
//#endregion
//#region src/player/telemetry.ts
function Vt(e, t, n = {}) {
	if (!t) return;
	let r = 0, i = 0, a = 0, s = null;
	t.addEventListener("seeking", () => {
		a++;
	});
	let c = (e) => e ? document.querySelector(e) : null, u = () => {
		let r = l(e.duration) || l(t.duration);
		if (!r) return;
		let i = Math.min(t.currentTime / r, 1), a = c(n.watched), o = c(n.mark), s = c(n.ratio);
		a && (a.style.width = `${(i * 100).toFixed(1)}%`), o && (o.style.left = `${(i * 100).toFixed(1)}%`), s && (s.textContent = `${(i * 100).toFixed(0)}%`);
	}, d = (n) => {
		let r = l(e.duration) || l(t.duration);
		!i && !n && !a || (o("/api/activity", {
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
	}, f = () => {
		s &&= (clearInterval(s), null);
	};
	t.onplay = () => {
		r = t.currentTime, f(), s = setInterval(() => d(!1), 1e4);
	}, t.ontimeupdate = () => {
		let e = t.currentTime - r;
		e > 0 && e < 2 && (i += e), r = t.currentTime, u();
	}, t.onpause = () => {
		f(), d(!1);
	}, t.onended = () => {
		f(), d(!0), n.onEnded?.();
	}, t.addEventListener("emptied", () => {
		f(), d(!1);
	}, { once: !0 }), u();
}
//#endregion
//#region src/player/videojs.ts
var Ht = "/vendor/videojs/8.24.1/", Ut = (e) => new Promise((t, n) => {
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
}), Wt = () => globalThis.videojs, J = null;
function Gt() {
	let e = Wt();
	return e ? Promise.resolve(e) : (J ??= Ut(`${Ht}video.min.js`).then(() => Ut(`${Ht}lang/zh-CN.js`)).then(() => {
		let e = Wt();
		if (!e) throw Error("videojs unavailable");
		return e;
	}).catch((e) => {
		throw J = null, e;
	}), J);
}
//#endregion
//#region src/islands.ts
var Kt = {
	"catalog-filter": { react: "catalog-filter" },
	"catalog-grid": { react: "catalog-grid" },
	"data-cleanup": { react: "data-cleanup" },
	duplicates: { react: "duplicates" },
	"entity-body": { react: "entity-body" },
	"entity-filter": { react: "entity-filter" },
	"entity-hero": { react: "entity-hero" },
	"follow-feed": { react: "follow-feed" },
	"follow-manage": { react: "follow-manage" },
	index: { react: "index" },
	"junk-queue": { react: "junk-queue" },
	"library-processing": { react: "library-processing" },
	playlists: { react: "playlists" },
	scraping: { react: "scraping" },
	"quality-goals": { react: "quality-goals" },
	review: { react: "review" },
	search: { react: "search" },
	configuration: { react: "configuration" },
	activity: { react: "activity" },
	stats: { react: "stats" },
	taste: { react: "taste" }
}, qt = () => import("/dist/peach-react.js").then(() => void 0), Jt = () => Object.keys(Kt), Y = /* @__PURE__ */ new Map();
async function Yt(e, t, n, r = {}) {
	let i = Kt[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	$t(t);
	let a = { controller: new AbortController() };
	Y.set(t, a);
	let o = (await import("/dist/peach-react.js")).pages[i.react];
	try {
		await o.prefetch(n, a.controller.signal);
	} catch {
		if (a.controller.signal.aborted) return;
	}
	if (!Zt(t, a, r)) return;
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
function Xt(e, t) {
	let n = e ? Y.get(e) : void 0;
	!n?.update || !n.props || (n.props = {
		...n.props,
		...t
	}, n.update(n.props));
}
function Zt(e, t, n) {
	return Y.get(e) === t ? n.isCurrent && !n.isCurrent() ? (Y.delete(e), !1) : !0 : !1;
}
var Qt = (e) => !!e && Y.has(e);
function $t(e) {
	for (let t of [...Y.keys()]) (t === e || e.contains(t)) && en(t);
}
function en(e) {
	let t = Y.get(e);
	t && (t.controller.abort(), Y.delete(e), t.dispose?.());
}
var tn = null;
function nn(e, t, n, r) {
	tn ??= import("/dist/peach-react.js").then((n) => (n.mountToaster(e, t), n)), tn.then((e) => e.showToast(n, r));
}
var X = null, Z = null;
function rn(e) {
	return X ??= import("/dist/peach-react.js").then((t) => (Z = t.configureStage(e), Z)), X;
}
var an = () => Z, Q = null, $ = null;
function on(e) {
	return Q ??= import("/dist/peach-react.js").then((t) => ($ = t.configureSettingsPanel(e), $)), Q;
}
var sn = () => $;
//#endregion
export { Xe as boardPageSkeleton, f as boundedPreference, Bt as cancelStreamSession, $e as catalogEmptyHtml, nt as catalogFilterSkeletonHtml, Qe as catalogSuggestions, pe as clampPage, pt as cleanupSkeletonHtml, Ft as clickPlayerControl, d as createSettingsStore, Ye as detailSkeletonHtml, Lt as directStreamSource, Gt as ensureVideojs, _e as entitySkeletonHtml, he as faceSourceScale, Pt as fmtSpeed, oe as followJobProgress, m as initBoardControls, Qt as islandMounted, Jt as islandNames, Ot as javImageKind, y as jobActivityHtml, Tt as junkCountSkeletonHtml, K as junkPath, gt as junkRoute, on as loadSettingsPanel, rn as loadStage, Yt as mountIsland, ge as nativeImageFit, It as newStreamSession, q as normalizeJavImage, Et as normalizeJavLayout, Dt as normalizeJavPreferences, fe as pageCount, me as paginationHtml, kt as panelFrame, zt as playableStreamSource, u as preferredDirection, qt as preloadIslands, jt as relayoutJavImages, le as selectGroup, se as selectRange, ce as selectionSummary, sn as settingsPanelApi, nn as showToast, rt as sidebarHasCatalogContent, ne as sidebarSectionHtml, at as sidebarTagCounts, an as stageApi, Nt as streamSpeedBits, p as syncBoardRange, At as syncJavImages, ue as syncSelectionToolbar, it as syncSidebarSurface, ie as transitionTheme, $t as unmountIsland, Xt as updateIsland, b as watchJob, re as wireSidebarGroups, Vt as wireTelemetry };
