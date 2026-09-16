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
//#region src/board-metrics.ts
var y = (e) => String(e ?? "").replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function b(e, t, n, r = "chart-no-axes-combined") {
	return `<span class="board-stat-label"><span class="board-stat-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><use href="#i-${/^[a-z0-9-]+$/.test(r) ? r : "database"}"/></svg></span>${y(e)}</span><b class="board-stat-value">${y(t)}</b><small class="board-stat-footer">${y(n || "当前记录")}</small>`;
}
function x(e, t, n) {
	if (!Number.isFinite(n) || n <= 0) return "";
	let r = Math.max(0, Math.min(n, Number.isFinite(t) ? t : 0)), i = r / n * 100;
	return `<div class="board-job-progress" role="progressbar" aria-label="${y(e)}" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${r}"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle class="board-job-track" cx="18" cy="18" r="15"/><circle class="board-job-fill" cx="18" cy="18" r="15" pathLength="100" stroke-dasharray="${i} ${100 - i}" transform="rotate(-90 18 18)"/></svg><span>${y(e)}<small>${Math.round(i)}%</small></span></div>`;
}
function S(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0), r = n.reduce((e, t) => e + t.score, 0);
	if (!r) return "";
	let i = 0, a = n.map((e, t) => {
		let n = e.score / r * 100, a = `<circle cx="100" cy="100" r="72" pathLength="100" fill="none" stroke="var(--chart-${t % 4})" stroke-width="22" stroke-dasharray="${n} ${100 - n}" stroke-dashoffset="${-i}"><title>${y(e.name)}：${e.score.toLocaleString()}</title></circle>`;
		return i += n, a;
	}).join("");
	return `<svg class="board-distribution" viewBox="0 0 200 200" role="img" aria-label="${y(t)}"><g transform="rotate(-90 100 100)">${a}</g><text x="100" y="100" text-anchor="middle" dominant-baseline="middle">${y(t)}</text></svg>`;
}
function C(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0).slice().sort((e, t) => t.score - e.score).slice(0, 8);
	if (!n.length) return "";
	let r = n[0].score, i = n.map((e) => `<li><span class="board-rank-fill" style="width:${(e.score / r * 100).toFixed(2)}%"></span><span>${y(e.name)}</span><b>${e.score.toLocaleString()}</b></li>`).join("");
	return `<ol class="board-ranked-chart" aria-label="${y(t)}">${i}</ol>`;
}
function w(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0).slice().sort((e, t) => t.score - e.score).slice(0, 6);
	if (n.length < 3) return "";
	let r = Math.max(...n.map((e) => e.score)), i = n.length, a = (e, t) => {
		let n = e / i * Math.PI * 2 - Math.PI / 2;
		return [160 + Math.cos(n) * t, 140 + Math.sin(n) * t];
	}, o = (e) => n.map((t, n) => a(n, e(n)).map((e) => e.toFixed(2)).join(",")).join(" "), s = [
		25,
		50,
		75,
		100
	].map((e) => `<polygon points="${o(() => e)}" class="board-radar-grid"/>`).join(""), c = n.map((e, t) => {
		let [n, r] = a(t, 116);
		return `<text x="${n}" y="${r}" text-anchor="${n < 145 ? "end" : n > 175 ? "start" : "middle"}">${y(e.name)}</text>`;
	}).join("");
	return `<svg class="board-radar" viewBox="0 0 320 280" role="img" aria-label="${y(t)}"><title>${y(n.map((e) => `${e.name} ${e.score}`).join("，"))}</title>${s}<polygon points="${o((e) => n[e].score / r * 100)}" class="board-radar-value"/>${c}</svg>`;
}
//#endregion
//#region src/board-controls.ts
function T(e) {
	let t = Number(e.min) || 0, n = Number(e.max) || 100, r = Number(e.value), i = n > t ? Math.max(0, Math.min(100, (r - t) / (n - t) * 100)) : 0;
	e.style.setProperty("--board-range-value", `${i}%`);
	let a = e.closest(".dual-range");
	if (!a) return;
	let o = e.id === "durMax" ? "max" : "min", s = a.querySelector(`[data-range-end="${o}"]`);
	s || (s = document.createElement("output"), s.className = "board-range-tip", s.dataset.rangeEnd = o, s.setAttribute("aria-hidden", "true"), a.append(s)), s.textContent = r >= n && o === "max" ? "不限" : `${r} 分钟`, s.style.left = `${i}%`, s.style.setProperty("--range-tip-shift", "0px");
	let c = a.getBoundingClientRect(), l = s.getBoundingClientRect(), u = l.right > c.right ? c.right - l.right : l.left < c.left ? c.left - l.left : 0;
	u && s.style.setProperty("--range-tip-shift", `${Math.round(u)}px`), a.querySelectorAll(".board-range-tip").forEach((e) => e.toggleAttribute("data-range-active", e === s));
}
function E() {
	let e = (e) => {
		e.querySelectorAll("input[type=range]").forEach(T), A(e), O(e), j(e);
	};
	e(document), new MutationObserver((t) => {
		for (let n of t) for (let t of n.addedNodes) t instanceof Element && (t.matches("input[type=range]") && T(t), e(t));
	}).observe(document.body, {
		subtree: !0,
		childList: !0
	}), document.addEventListener("input", (e) => {
		e.target instanceof HTMLInputElement && e.target.type === "range" && T(e.target);
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
var D = /* @__PURE__ */ new Map();
function O(e) {
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
			n(i), D.set(t, i);
		}, i = D.get(t);
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
var k = /* @__PURE__ */ new Map();
function A(e) {
	let t = ".iconswitch,.insightswitch,.insighttabs,.follow-workspace-switch", n = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && n.push(e), n.forEach((e) => {
		if (e.hasAttribute("data-board-segments") || e.closest("[data-skeleton]")) return;
		e.dataset.boardSegments = "true";
		let t = document.createElement("span");
		t.className = "board-segment-thumb", t.setAttribute("aria-hidden", "true"), e.prepend(t);
		let n = e.className + (e.getAttribute("aria-label") ?? ""), r = k.get(n) ?? null, a = () => {
			let a = e.querySelector("label:has(input:checked),button[aria-selected=true]");
			if (!a || !a.offsetWidth) return;
			let o = {
				x: a.offsetLeft,
				y: a.offsetTop,
				w: a.offsetWidth,
				h: a.offsetHeight
			};
			i(t, r, o, "x"), r = o, k.set(n, o);
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
function j(e) {
	let t = ".board-ranked-chart,.board-radar,.tasteranks,.board-heat-card,.board-sankey-card", n = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && n.push(e), n.forEach((e) => {
		if (e.hasAttribute("data-board-chart")) return;
		e.dataset.boardChart = "true", e.addEventListener("animationend", () => {
			e.getAnimations?.({ subtree: !0 }).some((e) => e.playState === "running") || e.classList.add("board-chart-settled");
		});
		let t = () => e.classList.add("board-chart-visible");
		if (typeof IntersectionObserver > "u" || matchMedia("(prefers-reduced-motion: reduce)").matches) {
			t();
			return;
		}
		let n = new IntersectionObserver((e) => {
			e.some((e) => e.isIntersecting) && (n.disconnect(), t());
		}, { threshold: .15 });
		n.observe(e);
	});
}
function M(e) {
	e.querySelectorAll(".tasteranks,.insightranking").forEach((e, t) => {
		if (e.children.length <= 5 || e.parentElement?.hasAttribute("data-expandable-ranks")) return;
		let n = document.createElement("div");
		n.className = "board-expand-ranks", n.dataset.expandableRanks = "", e.before(n), n.append(e), e.id = e.id || `board-rank-list-${t}`, e.classList.add("board-rank-list");
		let r = document.createElement("button");
		r.type = "button", r.className = "board-rank-expand", r.setAttribute("aria-controls", e.id), r.setAttribute("aria-expanded", "false"), r.setAttribute("aria-label", "展开更多排名"), r.innerHTML = "<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><use href=\"#i-chevron-down\"/></svg>", n.append(r);
		let i = () => {
			let t = e.children[4];
			e.offsetWidth && (n.style.setProperty("--rank-collapsed-height", `${t.offsetTop - e.offsetTop + t.offsetHeight}px`), n.style.setProperty("--rank-expanded-height", `${e.scrollHeight}px`));
		}, a = () => {
			let t = r.getAttribute("aria-expanded") === "true";
			n.classList.toggle("expanded", t), [...e.children].forEach((e, n) => e.inert = !t && n >= 5), i();
		}, o = (t) => {
			t.target === e && n.classList.remove("toggling");
		};
		e.addEventListener("transitionend", o), e.addEventListener("transitioncancel", o);
		let s = () => {
			let e = r.getBoundingClientRect().top, t = performance.now() + 300, n = () => {
				let i = r.getBoundingClientRect().top - e;
				i && window.scrollBy(0, i), performance.now() < t && requestAnimationFrame(n);
			};
			n();
		};
		r.onclick = () => {
			let e = r.getAttribute("aria-expanded") !== "true";
			r.setAttribute("aria-expanded", String(e)), r.setAttribute("aria-label", e ? "收起排名" : "展开更多排名"), n.classList.add("toggling"), a(), e || s();
		}, new ResizeObserver(i).observe(e), a();
	});
}
//#endregion
//#region node_modules/d3-array/src/max.js
function N(e, t) {
	let n;
	if (t === void 0) for (let t of e) t != null && (n < t || n === void 0 && t >= t) && (n = t);
	else {
		let r = -1;
		for (let i of e) (i = t(i, ++r, e)) != null && (n < i || n === void 0 && i >= i) && (n = i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-array/src/min.js
function P(e, t) {
	let n;
	if (t === void 0) for (let t of e) t != null && (n > t || n === void 0 && t >= t) && (n = t);
	else {
		let r = -1;
		for (let i of e) (i = t(i, ++r, e)) != null && (n > i || n === void 0 && i >= i) && (n = i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-array/src/sum.js
function F(e, t) {
	let n = 0;
	if (t === void 0) for (let t of e) (t = +t) && (n += t);
	else {
		let r = -1;
		for (let i of e) (i = +t(i, ++r, e)) && (n += i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-sankey/src/align.js
function I(e, t) {
	return e.sourceLinks.length ? e.depth : t - 1;
}
//#endregion
//#region node_modules/d3-sankey/src/constant.js
function L(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-sankey/src/sankey.js
function R(e, t) {
	return z(e.source, t.source) || e.index - t.index;
}
function ee(e, t) {
	return z(e.target, t.target) || e.index - t.index;
}
function z(e, t) {
	return e.y0 - t.y0;
}
function B(e) {
	return e.value;
}
function te(e) {
	return e.index;
}
function ne(e) {
	return e.nodes;
}
function re(e) {
	return e.links;
}
function ie(e, t) {
	let n = e.get(t);
	if (!n) throw Error("missing: " + t);
	return n;
}
function ae({ nodes: e }) {
	for (let t of e) {
		let e = t.y0, n = e;
		for (let n of t.sourceLinks) n.y0 = e + n.width / 2, e += n.width;
		for (let e of t.targetLinks) e.y1 = n + e.width / 2, n += e.width;
	}
}
function oe() {
	let e = 0, t = 0, n = 1, r = 1, i = 24, a = 8, o, s = te, c = I, l, u, d = ne, f = re, p = 6;
	function m() {
		let e = {
			nodes: d.apply(null, arguments),
			links: f.apply(null, arguments)
		};
		return h(e), g(e), _(e), v(e), x(e), ae(e), e;
	}
	m.update = function(e) {
		return ae(e), e;
	}, m.nodeId = function(e) {
		return arguments.length ? (s = typeof e == "function" ? e : L(e), m) : s;
	}, m.nodeAlign = function(e) {
		return arguments.length ? (c = typeof e == "function" ? e : L(e), m) : c;
	}, m.nodeSort = function(e) {
		return arguments.length ? (l = e, m) : l;
	}, m.nodeWidth = function(e) {
		return arguments.length ? (i = +e, m) : i;
	}, m.nodePadding = function(e) {
		return arguments.length ? (a = o = +e, m) : a;
	}, m.nodes = function(e) {
		return arguments.length ? (d = typeof e == "function" ? e : L(e), m) : d;
	}, m.links = function(e) {
		return arguments.length ? (f = typeof e == "function" ? e : L(e), m) : f;
	}, m.linkSort = function(e) {
		return arguments.length ? (u = e, m) : u;
	}, m.size = function(i) {
		return arguments.length ? (e = t = 0, n = +i[0], r = +i[1], m) : [n - e, r - t];
	}, m.extent = function(i) {
		return arguments.length ? (e = +i[0][0], n = +i[1][0], t = +i[0][1], r = +i[1][1], m) : [[e, t], [n, r]];
	}, m.iterations = function(e) {
		return arguments.length ? (p = +e, m) : p;
	};
	function h({ nodes: e, links: t }) {
		for (let [t, n] of e.entries()) n.index = t, n.sourceLinks = [], n.targetLinks = [];
		let n = new Map(e.map((t, n) => [s(t, n, e), t]));
		for (let [e, r] of t.entries()) {
			r.index = e;
			let { source: t, target: i } = r;
			typeof t != "object" && (t = r.source = ie(n, t)), typeof i != "object" && (i = r.target = ie(n, i)), t.sourceLinks.push(r), i.targetLinks.push(r);
		}
		if (u != null) for (let { sourceLinks: t, targetLinks: n } of e) t.sort(u), n.sort(u);
	}
	function g({ nodes: e }) {
		for (let t of e) t.value = t.fixedValue === void 0 ? Math.max(F(t.sourceLinks, B), F(t.targetLinks, B)) : t.fixedValue;
	}
	function _({ nodes: e }) {
		let t = e.length, n = new Set(e), r = /* @__PURE__ */ new Set(), i = 0;
		for (; n.size;) {
			for (let e of n) {
				e.depth = i;
				for (let { target: t } of e.sourceLinks) r.add(t);
			}
			if (++i > t) throw Error("circular link");
			n = r, r = /* @__PURE__ */ new Set();
		}
	}
	function v({ nodes: e }) {
		let t = e.length, n = new Set(e), r = /* @__PURE__ */ new Set(), i = 0;
		for (; n.size;) {
			for (let e of n) {
				e.height = i;
				for (let { source: t } of e.targetLinks) r.add(t);
			}
			if (++i > t) throw Error("circular link");
			n = r, r = /* @__PURE__ */ new Set();
		}
	}
	function y({ nodes: t }) {
		let r = N(t, (e) => e.depth) + 1, a = (n - e - i) / (r - 1), o = Array(r);
		for (let n of t) {
			let t = Math.max(0, Math.min(r - 1, Math.floor(c.call(null, n, r))));
			n.layer = t, n.x0 = e + t * a, n.x1 = n.x0 + i, o[t] ? o[t].push(n) : o[t] = [n];
		}
		if (l) for (let e of o) e.sort(l);
		return o;
	}
	function b(e) {
		let n = P(e, (e) => (r - t - (e.length - 1) * o) / F(e, B));
		for (let i of e) {
			let e = t;
			for (let t of i) {
				t.y0 = e, t.y1 = e + t.value * n, e = t.y1 + o;
				for (let e of t.sourceLinks) e.width = e.value * n;
			}
			e = (r - e + o) / (i.length + 1);
			for (let t = 0; t < i.length; ++t) {
				let n = i[t];
				n.y0 += e * (t + 1), n.y1 += e * (t + 1);
			}
			O(i);
		}
	}
	function x(e) {
		let n = y(e);
		o = Math.min(a, (r - t) / (N(n, (e) => e.length) - 1)), b(n);
		for (let e = 0; e < p; ++e) {
			let t = .99 ** e, r = Math.max(1 - t, (e + 1) / p);
			C(n, t, r), S(n, t, r);
		}
	}
	function S(e, t, n) {
		for (let r = 1, i = e.length; r < i; ++r) {
			let i = e[r];
			for (let e of i) {
				let n = 0, r = 0;
				for (let { source: t, value: i } of e.targetLinks) {
					let a = i * (e.layer - t.layer);
					n += k(t, e) * a, r += a;
				}
				if (!(r > 0)) continue;
				let i = (n / r - e.y0) * t;
				e.y0 += i, e.y1 += i, D(e);
			}
			l === void 0 && i.sort(z), w(i, n);
		}
	}
	function C(e, t, n) {
		for (let r = e.length - 2; r >= 0; --r) {
			let i = e[r];
			for (let e of i) {
				let n = 0, r = 0;
				for (let { target: t, value: i } of e.sourceLinks) {
					let a = i * (t.layer - e.layer);
					n += A(e, t) * a, r += a;
				}
				if (!(r > 0)) continue;
				let i = (n / r - e.y0) * t;
				e.y0 += i, e.y1 += i, D(e);
			}
			l === void 0 && i.sort(z), w(i, n);
		}
	}
	function w(e, n) {
		let i = e.length >> 1, a = e[i];
		E(e, a.y0 - o, i - 1, n), T(e, a.y1 + o, i + 1, n), E(e, r, e.length - 1, n), T(e, t, 0, n);
	}
	function T(e, t, n, r) {
		for (; n < e.length; ++n) {
			let i = e[n], a = (t - i.y0) * r;
			a > 1e-6 && (i.y0 += a, i.y1 += a), t = i.y1 + o;
		}
	}
	function E(e, t, n, r) {
		for (; n >= 0; --n) {
			let i = e[n], a = (i.y1 - t) * r;
			a > 1e-6 && (i.y0 -= a, i.y1 -= a), t = i.y0 - o;
		}
	}
	function D({ sourceLinks: e, targetLinks: t }) {
		if (u === void 0) {
			for (let { source: { sourceLinks: e } } of t) e.sort(ee);
			for (let { target: { targetLinks: t } } of e) t.sort(R);
		}
	}
	function O(e) {
		if (u === void 0) for (let { sourceLinks: t, targetLinks: n } of e) t.sort(ee), n.sort(R);
	}
	function k(e, t) {
		let n = e.y0 - (e.sourceLinks.length - 1) * o / 2;
		for (let { target: r, width: i } of e.sourceLinks) {
			if (r === t) break;
			n += i + o;
		}
		for (let { source: r, width: i } of t.targetLinks) {
			if (r === e) break;
			n -= i;
		}
		return n;
	}
	function A(e, t) {
		let n = t.y0 - (t.targetLinks.length - 1) * o / 2;
		for (let { source: r, width: i } of t.targetLinks) {
			if (r === e) break;
			n += i + o;
		}
		for (let { target: r, width: i } of e.sourceLinks) {
			if (r === t) break;
			n -= i;
		}
		return n;
	}
	return m;
}
//#endregion
//#region node_modules/d3-path/src/path.js
var se = Math.PI, ce = 2 * se, V = 1e-6, le = ce - V;
function ue() {
	this._x0 = this._y0 = this._x1 = this._y1 = null, this._ = "";
}
function de() {
	return new ue();
}
ue.prototype = de.prototype = {
	constructor: ue,
	moveTo: function(e, t) {
		this._ += "M" + (this._x0 = this._x1 = +e) + "," + (this._y0 = this._y1 = +t);
	},
	closePath: function() {
		this._x1 !== null && (this._x1 = this._x0, this._y1 = this._y0, this._ += "Z");
	},
	lineTo: function(e, t) {
		this._ += "L" + (this._x1 = +e) + "," + (this._y1 = +t);
	},
	quadraticCurveTo: function(e, t, n, r) {
		this._ += "Q" + +e + "," + +t + "," + (this._x1 = +n) + "," + (this._y1 = +r);
	},
	bezierCurveTo: function(e, t, n, r, i, a) {
		this._ += "C" + +e + "," + +t + "," + +n + "," + +r + "," + (this._x1 = +i) + "," + (this._y1 = +a);
	},
	arcTo: function(e, t, n, r, i) {
		e = +e, t = +t, n = +n, r = +r, i = +i;
		var a = this._x1, o = this._y1, s = n - e, c = r - t, l = a - e, u = o - t, d = l * l + u * u;
		if (i < 0) throw Error("negative radius: " + i);
		if (this._x1 === null) this._ += "M" + (this._x1 = e) + "," + (this._y1 = t);
		else if (d > V) {
			if (!(Math.abs(u * s - c * l) > V) || !i) this._ += "L" + (this._x1 = e) + "," + (this._y1 = t);
			else {
				var f = n - a, p = r - o, m = s * s + c * c, h = f * f + p * p, g = Math.sqrt(m), _ = Math.sqrt(d), v = i * Math.tan((se - Math.acos((m + d - h) / (2 * g * _))) / 2), y = v / _, b = v / g;
				Math.abs(y - 1) > V && (this._ += "L" + (e + y * l) + "," + (t + y * u)), this._ += "A" + i + "," + i + ",0,0," + +(u * f > l * p) + "," + (this._x1 = e + b * s) + "," + (this._y1 = t + b * c);
			}
		}
	},
	arc: function(e, t, n, r, i, a) {
		e = +e, t = +t, n = +n, a = !!a;
		var o = n * Math.cos(r), s = n * Math.sin(r), c = e + o, l = t + s, u = 1 ^ a, d = a ? r - i : i - r;
		if (n < 0) throw Error("negative radius: " + n);
		this._x1 === null ? this._ += "M" + c + "," + l : (Math.abs(this._x1 - c) > V || Math.abs(this._y1 - l) > V) && (this._ += "L" + c + "," + l), n && (d < 0 && (d = d % ce + ce), d > le ? this._ += "A" + n + "," + n + ",0,1," + u + "," + (e - o) + "," + (t - s) + "A" + n + "," + n + ",0,1," + u + "," + (this._x1 = c) + "," + (this._y1 = l) : d > V && (this._ += "A" + n + "," + n + ",0," + +(d >= se) + "," + u + "," + (this._x1 = e + n * Math.cos(i)) + "," + (this._y1 = t + n * Math.sin(i))));
	},
	rect: function(e, t, n, r) {
		this._ += "M" + (this._x0 = this._x1 = +e) + "," + (this._y0 = this._y1 = +t) + "h" + +n + "v" + +r + "h" + -n + "Z";
	},
	toString: function() {
		return this._;
	}
};
//#endregion
//#region node_modules/d3-shape/src/constant.js
function fe(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-shape/src/point.js
function pe(e) {
	return e[0];
}
function me(e) {
	return e[1];
}
//#endregion
//#region node_modules/d3-shape/src/array.js
var he = Array.prototype.slice;
//#endregion
//#region node_modules/d3-shape/src/link/index.js
function ge(e) {
	return e.source;
}
function _e(e) {
	return e.target;
}
function ve(e) {
	var t = ge, n = _e, r = pe, i = me, a = null;
	function o() {
		var o, s = he.call(arguments), c = t.apply(this, s), l = n.apply(this, s);
		if (a ||= o = de(), e(a, +r.apply(this, (s[0] = c, s)), +i.apply(this, s), +r.apply(this, (s[0] = l, s)), +i.apply(this, s)), o) return a = null, o + "" || null;
	}
	return o.source = function(e) {
		return arguments.length ? (t = e, o) : t;
	}, o.target = function(e) {
		return arguments.length ? (n = e, o) : n;
	}, o.x = function(e) {
		return arguments.length ? (r = typeof e == "function" ? e : fe(+e), o) : r;
	}, o.y = function(e) {
		return arguments.length ? (i = typeof e == "function" ? e : fe(+e), o) : i;
	}, o.context = function(e) {
		return arguments.length ? (a = e ?? null, o) : a;
	}, o;
}
function ye(e, t, n, r, i) {
	e.moveTo(t, n), e.bezierCurveTo(t = (t + r) / 2, n, t, i, r, i);
}
function be() {
	return ve(ye);
}
//#endregion
//#region node_modules/d3-sankey/src/sankeyLinkHorizontal.js
function xe(e) {
	return [e.source.x1, e.y0];
}
function Se(e) {
	return [e.target.x0, e.y1];
}
function Ce() {
	return be().source(xe).target(Se);
}
//#endregion
//#region src/board-sankey.ts
function we(e = []) {
	let t = e.filter((e) => e.source && e.target && Number.isFinite(e.value) && e.value > 0);
	if (!t.length) return "";
	let n = [...new Set(t.map((e) => e.source))], r = [...new Set(t.map((e) => e.target))], i = oe().nodeId((e) => e.id).nodeWidth(10).nodePadding(22).extent([[155, 16], [535, 404]])({
		nodes: [...n.map((e) => ({
			id: `source:${e}`,
			name: e,
			side: "source"
		})), ...r.map((e) => ({
			id: `target:${e}`,
			name: e,
			side: "target"
		}))],
		links: t.map((e) => ({
			source: `source:${e.source}`,
			target: `target:${e.target}`,
			value: e.value
		}))
	}), a = t.reduce((e, t) => e + t.value, 0), o = Ce(), s = i.links.map((e) => {
		let t = e.source, r = e.target;
		return `<path d="${o(e)}" stroke-width="${Math.max(.5, e.width || 0)}" style="--flow-color:var(--board-chart-${n.indexOf(t.name) % 6})" data-flow-source="${t.index}" data-flow-target="${r.index}" data-flow-value="${e.value}" data-flow-label="${d(t.name)} → ${d(r.name)}" tabindex="0" role="img" aria-label="${d(t.name)} → ${d(r.name)}：${e.value} 条线索"/>`;
	}).join(""), c = i.nodes.map((e) => `<g data-flow-node="${e.index}" data-flow-value="${e.value}" data-flow-label="${d(e.name)}" tabindex="0" role="img" aria-label="${d(e.name)}：${e.value} 条线索"><rect x="${e.x0}" y="${e.y0}" width="10" height="${Math.max(1, (e.y1 || 0) - (e.y0 || 0))}" rx="5" fill="${e.side === "source" ? `var(--board-chart-${n.indexOf(e.name) % 6})` : "var(--color-text-secondary)"}"/><text x="${e.side === "source" ? 145 : 545}" y="${((e.y0 || 0) + (e.y1 || 0)) / 2}" text-anchor="${e.side === "source" ? "end" : "start"}" dominant-baseline="middle">${d(e.name.length > 18 ? e.name.slice(0, 16) + "…" : e.name)}<tspan x="${e.side === "source" ? 145 : 545}" dy="15">${e.side === "source" ? e.value?.toLocaleString() : ((e.value || 0) / a * 100).toFixed(1) + "%"}</tspan></text></g>`).join("");
	return `<section class="board-sankey-card" data-sankey-card><header><h3>创作者线索来源</h3><b data-sankey-number>${a.toLocaleString()}</b><span data-sankey-label>条线索</span></header><div class="board-sankey-scroll"><svg viewBox="0 0 720 435" aria-label="来源网站与创作者线索"><g class="board-sankey-links">${s}</g><g class="board-sankey-nodes">${c}</g></svg></div><footer><span>来源网站</span><span>创作者 · 线索占比</span></footer></section>`;
}
function Te(e) {
	e.querySelectorAll("[data-sankey-card]").forEach((e) => {
		let t = [...e.querySelectorAll("[data-flow-source]")], n = [...e.querySelectorAll("[data-flow-node]")], r = e.querySelector("[data-sankey-number]"), i = e.querySelector("[data-sankey-label]"), a = r.textContent, o = () => {
			t.forEach((e) => e.style.opacity = ""), n.forEach((e) => e.style.opacity = ""), r.textContent = a, i.textContent = "条线索";
		};
		[...t, ...n].forEach((e) => {
			let a = () => {
				let a = e.dataset.flowNode;
				t.forEach((t) => t.style.opacity = String((a === void 0 ? t === e : t.dataset.flowSource === a || t.dataset.flowTarget === a) ? .7 : .08)), n.forEach((n) => n.style.opacity = String(a === void 0 ? n.dataset.flowNode === e.dataset.flowSource || n.dataset.flowNode === e.dataset.flowTarget ? 1 : .3 : n === e || t.some((e) => e.dataset.flowSource === a && e.dataset.flowTarget === n.dataset.flowNode || e.dataset.flowTarget === a && e.dataset.flowSource === n.dataset.flowNode) ? 1 : .3)), r.textContent = Number(e.dataset.flowValue).toLocaleString(), i.textContent = e.dataset.flowLabel;
			};
			e.addEventListener("pointerenter", a), e.addEventListener("pointerleave", o), e.addEventListener("focus", a), e.addEventListener("blur", o);
		});
	});
}
//#endregion
//#region src/board-analytics.ts
var H = (e) => Number.isFinite(e) && e >= 0;
function Ee(e, t, n = "个视频") {
	let r = e.filter((e) => H(e.value));
	if (!r.length) return "";
	let i = r.reduce((e, t) => e + t.value, 0), a = Math.max(1, ...r.map((e) => e.value)) * 1.1, o = Math.min(22, 110 / Math.max(1, r.length)), s = Math.min(15, o * .68), c = r.map((e, t) => {
		let r = 32 + t * o, i = e.value / a * 100;
		return `<g style="--ring-color:var(--board-chart-${t % 6});--ring-delay:${t * 60}ms"><circle class="board-ring-track" cx="160" cy="160" r="${r}" stroke-width="${s}"/><circle class="board-ring-value" data-radial-ring="${t}" tabindex="0" role="button" aria-label="${d(e.name)}：${e.value.toLocaleString()} ${d(n)}" aria-pressed="false" cx="160" cy="160" r="${r}" stroke-width="${s}" pathLength="100" stroke-dasharray="${i} ${100 - i}" style="--ring-length:${i}" transform="rotate(-90 160 160)"/></g>`;
	}).join("");
	return `<section class="board-radial-card" data-radial-card data-radial-total="${i}" data-radial-title="${d(t)}"><header><span data-radial-label>${d(t)}</span><b data-radial-number>${i.toLocaleString()}</b><small>${d(n)}</small></header><svg class="board-rings" viewBox="0 0 320 320" aria-label="${d(t)}">${c}</svg><div class="board-radial-tiles">${r.map((e, t) => `<button type="button" data-radial-tile="${t}" data-radial-value="${e.value}" data-radial-name="${d(e.name)}" aria-pressed="false" style="--ring-color:var(--board-chart-${t % 6})"><span><i aria-hidden="true"></i>${d(e.name)}</span><b>${e.value.toLocaleString()}</b>${e.detail ? `<small>${d(e.detail)}</small>` : ""}</button>`).join("")}</div></section>`;
}
function De(e) {
	e.querySelectorAll("[data-radial-card]").forEach((e) => {
		let t = [...e.querySelectorAll("[data-radial-tile]")], n = [...e.querySelectorAll("[data-radial-ring]")], r = e.querySelector("[data-radial-number]"), i = e.querySelector("[data-radial-label]"), a = -1, o = 0, s = 0, c = (c, l = 300) => {
			e.dataset.radialFocus = String(c), t.forEach((e, t) => {
				e.dataset.active = String(t === c), e.setAttribute("aria-pressed", String(t === a)), n[t]?.setAttribute("aria-pressed", String(t === a)), n[t] && (n[t].dataset.active = String(t === c));
			});
			let u = Number(c < 0 ? e.dataset.radialTotal : t[c]?.dataset.radialValue);
			i.textContent = c < 0 ? e.dataset.radialTitle : t[c].dataset.radialName, cancelAnimationFrame(s);
			let d = o, f = performance.now(), p = (t) => {
				if (!e.isConnected) return;
				let n = matchMedia("(prefers-reduced-motion: reduce)").matches ? 1 : Math.min(1, (t - f) / l);
				o = d + (u - d) * (1 - (1 - n) ** 3), r.textContent = Math.round(o).toLocaleString(), n < 1 && (s = requestAnimationFrame(p));
			};
			s = requestAnimationFrame(p);
		}, l = (e) => {
			a = a === e ? -1 : e, c(a);
		};
		[...t, ...n].forEach((e) => {
			let t = Number(e.getAttribute("data-radial-tile") ?? e.getAttribute("data-radial-ring"));
			e.addEventListener("pointerenter", () => c(t)), e.addEventListener("pointerleave", () => c(a)), e.addEventListener("focus", () => c(t)), e.addEventListener("blur", () => c(a)), e.addEventListener("click", () => l(t)), e instanceof SVGElement && e.addEventListener("keydown", (e) => {
				(e.key === "Enter" || e.key === " ") && (e.preventDefault(), l(t));
			});
		}), e.dataset.radialFocus = "-1", r.textContent = "0";
		let u = () => {
			requestAnimationFrame(() => {
				e.isConnected && (e.classList.add("board-chart-visible"), c(-1, 1200));
			});
		};
		if (typeof IntersectionObserver > "u" || matchMedia("(prefers-reduced-motion: reduce)").matches) u();
		else {
			let t = new IntersectionObserver((e) => {
				e.some((e) => e.isIntersecting) && (t.disconnect(), u());
			}, { threshold: .15 });
			t.observe(e);
		}
	});
}
var U = [
	"周一",
	"周二",
	"周三",
	"周四",
	"周五",
	"周六",
	"周日"
];
function Oe(e) {
	if (!e?.days?.length) return "<section class=\"board-activity-empty\"><h3>浏览活跃时间</h3><p>还没有可用于分析的口味网站访问记录。</p></section>";
	let t = Array.from({ length: 7 }, () => Array(24).fill(0));
	for (let n of e.hours || []) Number.isInteger(n.weekday) && n.weekday >= 0 && n.weekday < 7 && Number.isInteger(n.hour) && n.hour >= 0 && n.hour < 24 && H(n.count) && (t[n.weekday][n.hour] = (t[n.weekday][n.hour] || 0) + n.count);
	let n = Math.max(1, ...t.flat()), r = t.flat().reduce((e, t) => e + t, 0), i = t.map((e, t) => `<span class="board-heat-axis">${U[t]}</span>${e.map((e, r) => `<button type="button" data-heat-value="${e}" data-heat-label="${U[t]} ${r}:00" aria-label="${U[t]} ${r}:00，${e} 次访问" style="--heat:${e ? Math.max(12, e / n * 100) : 0}%"></button>`).join("")}`).join(""), a = e.days.filter((e) => /^\d{4}-\d{2}-\d{2}$/.test(e.date) && H(e.count)).sort((e, t) => e.date.localeCompare(t.date));
	if (!a.length) return "";
	let o = /* @__PURE__ */ new Date(`${a.at(-1).date}T00:00:00Z`), s = new Date(o);
	s.setUTCDate(s.getUTCDate() - 90);
	let c = new Map(a.map((e) => [e.date, e.count])), l = Math.max(1, ...a.map((e) => e.count)), u = Array.from({ length: 91 }, (e, t) => {
		let n = new Date(s);
		n.setUTCDate(s.getUTCDate() + t);
		let r = n.toISOString().slice(0, 10), i = c.get(r) || 0;
		return `<button type="button" data-heat-value="${i}" data-heat-label="${r}" aria-label="${r}，${i} 次访问" style="--heat:${i ? Math.max(12, i / l * 100) : 0}%"></button>`;
	}).join("");
	return `<div class="board-activity-charts"><section class="board-heat-card" data-heat-card><header><h3>浏览活跃时间</h3><b data-heat-number>${r.toLocaleString()}</b><span data-heat-title data-heat-default="口味网站访问">口味网站访问</span></header><div class="board-heat-scroll"><div class="board-hour-grid"><span></span>${Array.from({ length: 24 }, (e, t) => `<span class="board-heat-axis">${t % 2 ? "" : t}</span>`).join("")}${i}</div></div><footer>星期 × 小时<span>${d(e.timezone || "UTC+08:00")}</span></footer></section><section class="board-heat-card" data-heat-card><header><h3>每日活跃</h3><b data-heat-number>${a.filter((e) => e.date >= s.toISOString().slice(0, 10)).reduce((e, t) => e + t.count, 0).toLocaleString()}</b><span data-heat-title data-heat-default="口味网站访问">口味网站访问</span></header><div class="board-day-grid">${u}</div><footer>${s.toISOString().slice(0, 10)}<span>${a.at(-1).date}</span></footer></section></div>`;
}
function ke(e) {
	e.querySelectorAll("[data-heat-card]").forEach((e) => {
		let t = e.querySelector("[data-heat-number]"), n = e.querySelector("[data-heat-title]"), r = t.textContent;
		e.querySelectorAll("[data-heat-value]").forEach((e) => {
			let i = () => {
				t.textContent = Number(e.dataset.heatValue).toLocaleString(), n.textContent = e.dataset.heatLabel;
			}, a = () => {
				t.textContent = r, n.textContent = n.dataset.heatDefault;
			};
			e.addEventListener("pointerenter", i), e.addEventListener("pointerleave", a), e.addEventListener("focus", i), e.addEventListener("blur", a);
		});
	});
}
//#endregion
//#region src/sidebar-groups.ts
var W = (e) => e.replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function Ae(e, t, n = "", r = "") {
	if (!t) return "";
	let i = `sidebar-group-${encodeURIComponent(e)}`;
	return `<details class="sec${r ? " cat-" + W(r) : ""}" data-sidebar-group="${W(e)}"><summary role="button" class="board-section-toggle"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${W(e)}</span></summary><div class="board-sidebar-body" id="${i}">${t}${n}</div></details>`;
}
function je(e) {
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
var G = !1;
async function Me(e, t) {
	if (G) return;
	if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
		t();
		return;
	}
	let n = e.getBoundingClientRect(), r = n.left + n.width / 2, i = n.top + n.height / 2, a = Math.hypot(Math.max(r, innerWidth - r), Math.max(i, innerHeight - i)) * 2.5, o = document.createElement("style");
	o.textContent = `::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:radial-gradient(circle closest-side,#000 78%,#0006 88%,transparent);mask-repeat:no-repeat;will-change:mask-position,mask-size;animation:peach-theme-reveal 560ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${r}px ${i}px;mask-size:0px 0px}to{mask-position:${r - a / 2}px ${i - a / 2}px;mask-size:${a}px ${a}px}}`, G = !0, document.head.append(o);
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
		delete s.dataset.themeSnapshot, o.remove(), G = !1;
	}
}
//#endregion
//#region src/jobs.ts
function Ne(e, t = 0, n = 0) {
	return n > 0 ? x(e, t, n) : r(e);
}
async function Pe(e) {
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
function Fe(e) {
	let t = e.note || ((e) => a(e, {
		label: "任务状态",
		variant: "error"
	})), n = e.loading || r, i = e.progress || ((e, t, n) => Ne(n || `已处理 ${e} / ${t}`, e, t)), o = e.container || ((e) => `<section class="followtask" data-geist-fieldset aria-label="任务进度"><div class="geist-fieldset-content">${e}</div></section>`), s = document.createElement("div");
	e.host.hidden = !0, s.dataset.followJob = "", s.setAttribute("aria-live", "polite"), e.host.prepend(s);
	let c = e.storageKey || "peach-follow-job", l = sessionStorage.getItem(c) || void 0, u = !1;
	Pe({
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
var Ie = (e = "") => /^https?:\/\//i.test(e) ? e : "";
function Le(e = "") {
	let t = Ie(e) || (e.startsWith("/") && !e.startsWith("//") ? e : "");
	return `<div class="reviewimage" data-review-picture><span class="reviewimageempty"${t ? " hidden" : ""}>未取得来源图片</span>${t ? `<img src="${d(t)}" alt="来源候选图片" loading="lazy">` : ""}</div>`;
}
function Re(e) {
	let t = Ie(e.profile_url), n = (e.preview_assets || []).slice(0, 6), r = Math.max(0, Number(e.video_count || e.videos || 0));
	return `<section class="reviewidentityevidence"><h5>候选身份：${d(e.babepedia_name || "未标注")}</h5>
    <div class="reviewevidenceactions">${t ? `<a class="geist-button externallink" href="${d(t)}" target="_blank" rel="noopener noreferrer">来源资料<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a>` : ""}
    <button type="button" class="geist-button" data-entity-kind="creator" data-entity-name="${d(e.creator || "")}">查看全部 ${r.toLocaleString()} 部作品</button></div>
    ${Le(e.preview_url)}
    <p>通过后记录身份判断。</p>
    ${n.length ? `<h5>本地作品样本</h5><div class="reviewevidencesamples">${n.map((e) => `<div class="reviewevidencesample">
      <button class="geist-button" type="button" data-review-open-item="${e.id}"><span data-middle-truncate title="${d(e.name)}">${d(e.name)}</span></button>
      <button class="geist-button" type="button" data-review-reveal="${e.id}" aria-label="打开 ${d(e.name)} 的文件位置">文件位置</button>
    </div>`).join("")}</div>` : "<p>暂无本地作品样本，打开全部作品核对。</p>"}</section>`;
}
function ze(e) {
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
var Be = (e) => p(e);
//#endregion
//#region src/selection.ts
function Ve(e, t, n, r, i, a = i || !e.has(r)) {
	let o = n === null ? -1 : t.indexOf(n), s = t.indexOf(r);
	return i && o >= 0 && s >= 0 ? t.slice(Math.min(o, s), Math.max(o, s) + 1).forEach((t) => e.add(t)) : a ? e.add(r) : e.delete(r), r;
}
function He(e, t) {
	let n = t.filter((t) => e.has(t)).length;
	return {
		count: n,
		all: n > 0 && n === t.length,
		mixed: n > 0 && n < t.length
	};
}
function Ue(e, t, n) {
	t.forEach((t) => n ? e.add(t) : e.delete(t));
}
function We({ count: e, label: t, all: n, summary: r, actions: i, locked: a = !1 }) {
	e && (e.textContent = t), n && (n.checked = r.all, n.indeterminate = r.mixed);
	for (let e of i) e.disabled = !r.count || a;
}
//#endregion
//#region src/review-bulk.ts
var Ge = () => ({
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
function Ke(e) {
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
function qe(e, t) {
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
function Je(e, t) {
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
function Ye(e, t, n, r, i) {
	e.anchor = Ve(e.selected, t, e.anchor, n, r, i);
}
async function Xe(e, t, n, r) {
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
				message: Be(e)
			});
		}
	}
	return {
		completed: a,
		failures: i
	};
}
function Ze(e) {
	return e.length ? [...new Set(e.flatMap((e) => e.candidates?.map((e) => e.source || "") || []))].filter((t) => t && e.every((e) => e.candidates?.filter((e) => e.source === t).length === 1)) : [];
}
function Qe(e, n) {
	let r = e.querySelector(".reviewlist");
	if (!r || !n.rows.length || n.locked) return;
	let i = n.state, a = [...r.querySelectorAll("[data-review-key]")];
	n.category !== void 0 && i.category !== n.category && (i.category = n.category, i.filter = "", i.groupBy = "candidates", i.anchor = null);
	let s = n.catalog || n.rows, l = qe(s, n.metadata);
	l.some((e) => e[0] === i.groupBy) || (i.groupBy = "candidates", i.filter = "");
	let d = Je(s, i.groupBy);
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
			Ue(i.selected, e, !e.every((e) => i.selected.has(e))), L();
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
				Ye(i, p().map((e) => e.dataset.reviewKey), n, e, t), L();
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
						a && (i.anchor === null && (i.anchor = n), Ye(i, r.map((e) => e.dataset.reviewKey), a.dataset.reviewKey, !0, !0), L(), a.querySelector(".reviewpickitem input")?.focus());
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
		w.innerHTML = f(t ? "check-check-outline" : "check-check") + (t ? "清空当前选择" : i.filter ? "全选当前分类" : "全选本页"), w.setAttribute("aria-pressed", String(t)), j.hidden = !e.length, We({
			count: D,
			label: `已选 ${e.length} 项`,
			summary: He(i.selected, p().map((e) => e.dataset.reviewKey)),
			actions: [T, E]
		}), T.disabled ||= e.some((e) => !g(e));
		let r = Ze(h());
		O.hidden = !n.metadata || !h().some((e) => (e.candidates?.length || 0) > 1);
		let a = e.length && !r.length ? "所选项目无共同来源" : "统一选择来源", s = JSON.stringify([a, r]);
		if (s !== I) {
			I = s, O.innerHTML = o([["", a], ...r.map((e) => [e, e])], "", { label: "统一选择来源" });
			let e = u(O.firstElementChild);
			e.disabled = !r.length, e.addEventListener("change", () => {
				if (!(i.busy || !Ze(h()).includes(e.value))) {
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
		let u = 0, d = await Xe(a, async (e) => {
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
	L(), Ke(e);
}
function $e(e, t, n = 1) {
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
function et(e, t) {
	return Math.max(1, Math.ceil(e / t));
}
function tt(e, t) {
	return Math.min(Math.max(1, Math.floor(e) || 1), t);
}
function nt(e, t, n) {
	if (t <= 1) return "";
	let r = $e(e, t).map((t) => t === "…" ? "<li class=\"board-page-dots\" aria-hidden=\"true\">…</li>" : `<li><button type="button" class="board-page" data-page="${t}" aria-label="第 ${t} 页"${t === e ? " aria-current=\"page\"" : ""}>${t}</button></li>`).join("");
	return `<nav class="board-pagination" aria-label="${n}">
    <button type="button" class="geist-button" data-page="${e - 1}"${e <= 1 ? " disabled" : ""}><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-left"></use></svg>上一页</button>
    <ul>${r}</ul>
    <button type="button" class="geist-button" data-page="${e + 1}"${e >= t ? " disabled" : ""}>下一页<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"></use></svg></button>
  </nav>`;
}
//#endregion
//#region src/native-image.ts
function rt(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function it(e, t, n, r, i = 1) {
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
function at(e, t, n) {
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
var K = (e = "60%") => `<span class="skeleton" style="width:${e}"></span>`, q = () => `${K("80%")}${K("48%")}`, J = (e, t) => e.repeat(t), ot = (e, t = "metricstrip") => `<div class="${t}">${e.map((e) => `<div class="tastesummary"><span class="board-stat-label">${e}</span><b class="board-stat-value">${K("45%")}</b><small class="board-stat-footer">${K("60%")}</small></div>`).join("")}</div>`, st = (e, t = "skeleton-tabs") => `<div class="${t}">${e.map((e) => `<span>${e}</span>`).join("")}</div>`, ct = (e, t) => `<div class="${t} skeleton-segments" data-board-segments="true">${e.map((e, t) => `<span${t === 0 ? " class=\"skeleton-segment-selected\"" : ""}>${e}</span>`).join("")}</div>`, lt = (e) => `<section class="board-radial-card"><header><span>${e}</span><b>${K()}</b></header><div class="board-rings skeleton-rings"><span class="skeleton skeleton-ring"></span></div><div class="skeleton-lines">${q()}</div></section>`, Y = (e) => `<section class="insightpanel"><header>${e}</header><div class="insightpanelbody skeleton-lines">${J(q(), 3)}</div></section>`, ut = (e) => `<button class="fbtn" type="button" disabled>${e}</button>`, dt = (e) => `<div class="fsechead" data-collapse-toolbar><h3>关注列表</h3><span class="fmeta">${K("100px")}</span><div class="followtoolbaractions"><button class="fbtn primary followcheckall" disabled>${f("refresh-cw")}<span data-collapse-label>检查全部</span></button><div class="iconswitch" data-board-segments="true"><label>${f("layout-grid")}</label><label>${f("table")}</label></div><span class="fmanagesort" data-collapse-field>${f("sort")}${o([["checked", "检查时间"]], "checked", {
	label: "关注列表排序",
	attr: "disabled"
})}</span><button class="fbtn fmanagedir" disabled>${f("arrow-down")}</button>${e ? "" : ut(f("chevron-up") + "<span data-collapse-label>全部收起</span>")}</div></div>`, ft = () => `<div class="fsource frow"><span class="fchannelcheck">${K("18px")}</span><b>${K("85%")}</b><span class="fprovider">${K("54px")}</span><span class="fmeta fchecked">${K("40px")}</span><span class="fsourceactions"><span class="skeleton skeleton-icon"></span><span class="skeleton skeleton-icon"></span></span></div>`, pt = () => `<details class="fauthor" open><summary class="fauthorhead"><span class="favatar skeleton"></span><b>${K("90px")}</b><span class="skeleton skeleton-icon"></span><span class="fmeta">${K("40px")}</span><span class="board-author-actions"><button type="button" class="fbtn small" data-follow-author-select disabled>${f("check-check")}<span data-author-select-label>全选</span></button><span class="skeleton skeleton-icon"></span></span></summary><div class="fauthorsources">${J(ft(), 3)}</div></details>`;
function mt() {
	return `<div data-skeleton="detail" role="status" aria-label="正在读取作品详情"><div class="sgrid" aria-hidden="true"><div class="vwrap skeleton-detail-media skeleton"></div><aside class="side"><div class="sidecontent skeleton-lines">${K("85%")}${K("65%")}${J(q(), 4)}</div></aside></div></div>`;
}
function ht(e, n = {}) {
	let r = "";
	if (e === "/stats") r = `<div class="insightpage statsdashboard"><header class="insighttoolbar">${K("38%")}</header>${ot([
		"馆藏视频",
		"看过",
		"内容标签",
		"使用空间"
	])}<section class="insightdetail"><div class="insightdetailbody"><div class="board-inventory-charts">${lt("网盘与本地")}${lt("媒体库")}</div></div></section>${Y("内容标签")}</div>`;
	else if (e === "/taste") r = `<div class="tastepage"><header class="tastehead">${ct(["浏览器记录", "Peach 内部"], "insightswitch")}${K("24%")}</header><div class="tastestate"></div>${ot([
		"浏览记录",
		"口味维度",
		"浏览候选",
		"私有导出"
	], "tastesummaries")}<section class="tastehero"><div class="insightcopy"><span>浏览器画像</span><div class="skeleton skeleton-radar"></div></div><div class="tastebars skeleton-lines">${J(q(), 4)}</div></section>${Y("口味分析")}<div class="board-activity-charts">${Y("浏览活动")}${Y("时间分布")}</div>${Y("标签")}</div>`;
	else if (e === "/follow-manage") {
		let e = n.followLayout === "table", i = e ? `<div class="ftableframe"><div class="ftablewrap"><table class="ftable"><thead><tr>${[
			"选择",
			"创作者",
			"来源",
			"站点",
			"状态",
			"上次检查",
			"操作"
		].map((e) => `<th>${e === "选择" ? "<label>" + t("disabled aria-label=\"全选本页来源\"") + "</label>" : e}</th>`).join("")}</tr></thead><tbody>${J(`<tr>${[
			"20px",
			"90px",
			"120px",
			"60px",
			"40px",
			"100px",
			"60px"
		].map((e) => `<td>${K(e)}</td>`).join("")}</tr>`, 6)}</tbody></table></div></div>` : `<div class="board-follow-list">${J(pt(), 4)}</div>`;
		r = `<div class="follow followmanage"><div class="fmanageoverview">${[
			"关注创作者",
			"启用来源",
			"检查失败",
			"未看更新"
		].map((e) => `<div><span>${e}</span><b>${K()}</b></div>`).join("")}</div>${ct([
			"关注列表",
			"添加关注",
			"来源和凭证"
		], "follow-workspace-switch")}<div class="fmain"><section class="fsec" data-follow-workspace-panel="list">${dt(e)}<div class="board-follow-selection"${e ? " hidden" : ""}><label>${t("disabled")}全选本页</label></div><div class="frows fsources" data-layout="${e ? "table" : "default"}">${i}<div class="followpagefooter"><div class="followpageinfo">${K("120px")}${K("100px")}</div></div></div></section></div></div>`;
	} else if (e === "/configuration") r = `<div class="configpage">${st([
		"通用",
		"媒体",
		"网络与访问",
		"更新与维护"
	])}<section class="configfieldset"><div class="geist-fieldset-content"><h3 class="geist-fieldset-title">开机自启</h3><div class="skeleton-lines">${J(`<div class="skeleton-setting">${K("35%")}<span class="skeleton skeleton-toggle"></span></div>`, 3)}</div></div><footer class="geist-fieldset-footer">${K("100px")}</footer></section></div>`;
	else if (e === "/activity") r = `<div class="activitypage">${[
		"正在进行",
		"被挡下的",
		"最近完成"
	].map((e) => `<section class="activitysection"><h3 class="geist-fieldset-title">${e}</h3><div class="activity-runs"><article class="cleanupfieldset activity-run"><div class="geist-fieldset-content skeleton-lines">${K("35%")}${q()}</div></article></div></section>`).join("")}</div>`;
	else if (e === "/duplicates") r = `<div class="review"><div class="collection-summary">${K("38%")}</div><div class="fsechead dupactions"><h3>批量保留</h3>${K("40%")}</div>${J(`<section class="dupgroup"><div class="duphead">${K("45%")}</div><div class="duplist">${J(`<div class="duprow"><span class="dupcover skeleton"></span><span class="dupmarks">${K()}</span><span class="dupname">${K("90%")}</span>${K()}${K()}${K()}<span class="duppath">${K("70%")}</span></div>`, 2)}</div></section>`, 2)}</div>`;
	else if (e === "/quality-goals") r = `<div class="quality-workspace"><div class="collection-summary"><strong>待升级</strong>${K("20%")}</div><div class="qualitylist">${J(`<article class="qualityitem"><span class="qualitycover skeleton"></span><div class="qualitybody skeleton-lines">${q()}</div><footer class="qualityactions">${K("80%")}</footer></article>`, 6)}</div></div>`;
	else if (e === "/playlists") r = `<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><div class="playlistcreate skeleton-lines"><span>新播放列表</span>${K("200px")}</div></header><div class="playlistcards">${J(`<article class="card playlistcard"><div class="mixstack"><div class="pic skeleton"></div></div><div class="mixmeta"><span class="mav skeleton"></span><div class="mixcopy skeleton-lines">${q()}</div></div></article>`, 6)}</div></section>`;
	else return "";
	return `<div class="board-page-skeleton" data-skeleton="board${e}" role="status" aria-label="正在读取页面"><div aria-hidden="true" inert>${r}</div></div>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var gt = [
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
function _t() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function vt(e, t) {
	let n = new URLSearchParams();
	for (let t of gt) e[t] && n.set(t, e[t]);
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
function yt({ kind: e = "catalog", filtered: t = !1, jav: r = !1, configurable: i = !1, online: a = !1 } = {}) {
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
function bt(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function xt(e, t) {
	return e.dataset.surface?.split("?")[0] === t.split("?")[0] && e.querySelector(".dnav") ? (e.dataset.surface = t, !1) : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function St(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function Ct(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function wt(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function Tt() {
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
function Et(e, t = !1, n = !1) {
	if (t || n) return "";
	let r = "<svg class=\"externalmark\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><use href=\"#i-external-link\"></use></svg>";
	return `<details class="taste-history-guide"${e ? " open" : ""}>
    <summary><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"></use></svg>浏览器历史记录导入指南</summary>
    <div class="taste-history-guide-content">
      <p>在运行 Peach 的电脑上使用浏览器：点击上方「读取 Peach 主机」。</p>
      <p>记录在其他设备上：导出文件后，点击上方「导入历史」。多台设备的文件分别导入。</p>
      <ul><li>Chrome：在 <a class="externallink" href="https://takeout.google.com/" target="_blank" rel="noreferrer">Google Takeout${r}</a> 选择 Chrome 历史记录，下载 ZIP 后直接导入。</li>
      <li>其他浏览器：使用 <a class="externallink" href="https://github.com/purarue/browserexport" target="_blank" rel="noreferrer">browserexport${r}</a> 导出历史记录，再导入导出文件。</li></ul>
      <p>需要刷新时再次读取或导入；数据源可在页面底部移除。</p>
      <button type="button" class="geist-button taste-guide-skip">跳过</button>
    </div></details>`;
}
var Dt = "peach-taste-guide-dismissed";
function Ot(e, t) {
	l(e, ".taste-history-guide", "taste-guide-collapse");
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(Dt, "1"), n.remove();
	});
}
//#endregion
//#region src/resource-sync.ts
var X = (e = 0) => Number(e).toLocaleString(), kt = {
	local: "本地磁盘",
	115: "115",
	pikpak: "PikPak"
}, At = (t) => s(e[t] ?? "database"), Z = (e, t, n) => `<article class="board-plain-stat resourcestat">
    <span class="board-plain-stat-head">${e}</span>
    <strong>${t}</strong>
    <span class="cleanupmeta">${n}</span></article>`;
function jt(e, t) {
	let n = e.cache || {
		files: 0,
		bytes: 0
	}, r = !!(e.missing || n.files);
	return `<div class="cleanupstats resourcestats">${(e.sources || []).map((e) => Z(`<span class="board-stat-tile resourcestat-tile">${At(e.location)}</span>${kt[e.location] || "媒体来源"}<span class="resourcestat-state ${e.online ? "online" : "offline"}">${e.online ? "可访问" : "离线，已跳过"}</span>`, e.online ? `${X(e.missing)} 项` : "—", [e.online ? `找不到文件 · 已检查 ${X(e.checked)} 项` : `馆藏中有 ${X(e.total)} 项`, e.unreadable ? `${X(e.unreadable)} 项读取失败，已跳过` : ""].filter(Boolean).join(" · "))).join("")}
    ${Z("待移入回收站", `${X(e.missing)} 项`, "")}
    ${Z("可清理的缓存", `${X(n.files)} 个`, n.files ? t(n.bytes) : "")}</div>
    ${r ? a(`将把找不到文件的 ${X(e.missing)} 项馆藏记录移入回收站，并清理 ${X(n.files)} 个闲置缓存。`, { label: "清理内容" }) : ""}
    <div class="resourceapplyrow geist-fieldset-footer" data-geist-fieldset-footer>${r ? "<button class=\"geist-button primary\" type=\"button\" id=\"resourceApply\">清理失效记录与缓存</button>" : "<p class=\"resourcesyncok\">已检查可访问的来源，没有待清理的记录或缓存。</p>"}</div>`;
}
//#endregion
//#region src/jav-artwork.ts
function Mt(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function Nt(e) {
	return {
		javLayout: Mt(e.javLayout),
		javImage: Q(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function Q(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function Pt(e, t) {
	return e.is_jav && e.code && e.has_cover && (Q(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function Ft(e, t) {
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
function It(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (Q(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.classList.remove("panel"), e.removeAttribute("style"), e.closest(".pic")?.style.removeProperty("--cover-blur"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var Lt = {
	"avatar-picker": { react: "avatar-picker" },
	"library-processing": { react: "library-processing" },
	scraping: { react: "scraping" },
	"quality-goals": { react: "quality-goals" },
	configuration: { react: "configuration" },
	activity: { react: "activity" }
}, Rt = () => Object.keys(Lt), $ = /* @__PURE__ */ new Map();
async function zt(e, t, n, r = {}) {
	let i = Lt[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	Ht(t);
	let a = { controller: new AbortController() };
	$.set(t, a);
	let o = (await import("/dist/peach-react.js")).pages[i.react];
	try {
		await o.prefetch(n, a.controller.signal);
	} catch {
		if (a.controller.signal.aborted) return;
	}
	if (!Bt(t, a, r)) return;
	let s = t.ownerDocument.createElement("div");
	s.className = "peach-react", t.append(s);
	let c = o.mount(s, n);
	a.dispose = () => {
		c.unmount(), s.remove();
	};
}
function Bt(e, t, n) {
	return $.get(e) === t ? n.isCurrent && !n.isCurrent() ? ($.delete(e), !1) : (e.textContent = "", !0) : !1;
}
var Vt = (e) => !!e && $.has(e);
function Ht(e) {
	for (let t of [...$.keys()]) (t === e || e.contains(t)) && Ut(t);
}
function Ut(e) {
	let t = $.get(e);
	t && (t.controller.abort(), $.delete(e), t.dispose?.());
}
//#endregion
export { Dt as TASTE_GUIDE_KEY, Oe as activityChartsHtml, ht as boardPageSkeleton, g as boundedPreference, yt as catalogEmptyHtml, vt as catalogSuggestions, tt as clampPage, Tt as cleanupSkeletonHtml, Ct as cloudLocations, wt as cloudPreferenceLocations, Ge as createReviewSelection, we as creatorSankeyHtml, mt as detailSkeletonHtml, S as distributionChart, _t as emptyCatalogLayout, at as entitySkeletonHtml, Fe as followJobProgress, Je as groupReviewRows, Re as identityEvidenceHtml, E as initBoardControls, Vt as islandMounted, Rt as islandNames, Pt as javImageKind, Ne as jobActivityHtml, x as jobProgressHtml, rt as matchesFaceSource, zt as mountIsland, v as mountNumberSetting, it as nativeImageFit, Q as normalizeJavImage, Mt as normalizeJavLayout, Nt as normalizeJavPreferences, et as pageCount, nt as paginationHtml, Ft as panelFrame, m as preferredDirection, w as radarChart, Ee as radialCardHtml, C as rankedChart, jt as resourceScanHtml, Le as reviewImageHtml, Ue as selectGroup, Ve as selectRange, He as selectionSummary, bt as sidebarHasCatalogContent, Ae as sidebarSectionHtml, St as sidebarTagCounts, b as statCardBody, T as syncBoardRange, It as syncJavImages, _ as syncNumberSetting, We as syncSelectionToolbar, xt as syncSidebarSurface, Et as tasteHistoryGuideHtml, Me as transitionTheme, Ht as unmountIsland, Ke as updateReviewSticky, Pe as watchJob, ke as wireActivityCharts, Te as wireCreatorSankey, M as wireExpandableRanks, j as wireGrowingCharts, De as wireRadialCards, ze as wireReviewPictures, Qe as wireReviewSelection, je as wireSidebarGroups, Ot as wireTasteHistoryGuide };
