import { LOC as e, esc as t, faviconUrl as n, fmtDur as r, fmtSize as i, icon as a, requestErrorMessage as o } from "/js/core.js";
import { MEDIA_SOURCE_ICONS as s, checkboxHtml as c, confirmModal as l, emptyStateHtml as u, fieldsetTitle as d, loadingDotsHtml as f, noteHtml as p, progressHtml as m, projectBannerHtml as h, selectFieldHtml as g, selectOptionIconHtml as _, setActionBusy as v, wireCollapse as y, wireSelectField as b } from "/js/ui-components.js";
//#region node_modules/preact/dist/preact.module.js
var x, S, C, w, T, E, D, O, k, A, j, ee, M, te, N, P = {}, ne = [], re = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, ie = Array.isArray;
function F(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function ae(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function oe(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? x.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return se(e, o, r, i, null);
}
function se(e, t, n, r, i) {
	var a = {
		type: e,
		props: t,
		key: n,
		ref: r,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: i ?? ++C,
		__i: -1,
		__u: 0
	};
	return i == null && S.vnode != null && S.vnode(a), a;
}
function I(e) {
	return e.children;
}
function ce(e, t) {
	this.props = e, this.context = t;
}
function L(e, t) {
	if (t == null) return e.__ ? L(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? L(e) : null;
}
function le(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = F({}, t);
		a.__v = t.__v + 1, S.vnode && S.vnode(a), be(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? L(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, Se(r, a, i), t.__e = t.__ = null, a.__e != n && ue(a);
	}
}
function ue(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), ue(e);
}
function de(e) {
	(!e.__d && (e.__d = !0) && T.push(e) && !fe.__r++ || E != S.debounceRendering) && ((E = S.debounceRendering) || D)(fe);
}
function fe() {
	try {
		for (var e, t = 1; T.length;) T.length > t && T.sort(O), e = T.shift(), t = T.length, le(e);
	} finally {
		T.length = fe.__r = 0;
	}
}
function pe(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || ne, v = t.length;
	for (c = me(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || P, p.__i = d, g = be(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && Te(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = he(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function me(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = se(null, o, null, null, null) : ie(o) ? o = e.__k[a] = se(I, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = se(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = ge(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = L(s)), Ee(s, s));
	return r;
}
function he(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = he(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = L(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function ge(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function _e(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || re.test(t) ? n : n + "px";
}
function ve(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || _e(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || _e(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(ee, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[j] = r[j] : (n[j] = M, e.addEventListener(t, a ? N : te, a)) : e.removeEventListener(t, a ? N : te, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function ye(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[A] == null) t[A] = M++;
			else if (t[A] < n[j]) return;
			return n(S.event ? S.event(t) : t);
		}
	};
}
function be(e, t, n, r, i, a, o, s, c, l) {
	var u, d, f, p, m, h, g, _, v, y, b, x, C, w, T, E, D = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (u = S.__b) && u(t);
	n: if (typeof D == "function") {
		d = o.length;
		try {
			if (v = t.props, y = D.prototype && D.prototype.render, b = (u = D.contextType) && r[u.__c], x = u ? b ? b.props.value : u.__ : r, n.__c ? _ = (f = t.__c = n.__c).__ = f.__E : (y ? t.__c = f = new D(v, x) : (t.__c = f = new ce(v, x), f.constructor = D, f.render = De), b && b.sub(f), f.state || (f.state = {}), f.__n = r, p = f.__d = !0, f.__h = [], f._sb = []), y && f.__s == null && (f.__s = f.state), y && D.getDerivedStateFromProps != null && (f.__s == f.state && (f.__s = F({}, f.__s)), F(f.__s, D.getDerivedStateFromProps(v, f.__s))), m = f.props, h = f.state, f.__v = t, p) y && D.getDerivedStateFromProps == null && f.componentWillMount != null && f.componentWillMount(), y && f.componentDidMount != null && f.__h.push(f.componentDidMount);
			else {
				if (y && D.getDerivedStateFromProps == null && v !== m && f.componentWillReceiveProps != null && f.componentWillReceiveProps(v, x), t.__v == n.__v || !f.__e && f.shouldComponentUpdate != null && !1 === f.shouldComponentUpdate(v, f.__s, x)) {
					t.__v != n.__v && (f.props = v, f.state = f.__s, f.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), ne.push.apply(f.__h, f._sb), f._sb = [], f.__h.length && o.push(f), s = L(n);
					break n;
				}
				f.componentWillUpdate != null && f.componentWillUpdate(v, f.__s, x), y && f.componentDidUpdate != null && f.__h.push(function() {
					f.componentDidUpdate(m, h, g);
				});
			}
			if (f.context = x, f.props = v, f.__P = e, f.__e = !1, C = S.__r, w = 0, y) f.state = f.__s, f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), ne.push.apply(f.__h, f._sb), f._sb = [];
			else do
				f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), f.state = f.__s;
			while (f.__d && ++w < 25);
			f.state = f.__s, f.getChildContext != null && (r = F(F({}, r), f.getChildContext())), y && !p && f.getSnapshotBeforeUpdate != null && (g = f.getSnapshotBeforeUpdate(m, h)), T = u != null && u.type === I && u.key == null ? Ce(u.props.children) : u, s = pe(e, ie(T) ? T : [T], t, n, r, i, a, o, s, c, l), f.base = t.__e, t.__u &= -161, f.__h.length && o.push(f), _ && (f.__E = f.__ = null);
		} catch (e) {
			if (o.length = d, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (E = a.length; E--;) ae(a[E]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || xe(t), S.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = we(n.__e, t, n, r, i, a, o, c, l);
	return (u = S.diffed) && u(t), 128 & t.__u ? void 0 : s;
}
function xe(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(xe));
}
function Se(e, t, n) {
	for (var r = 0; r < n.length; r++) Te(n[r], n[++r], n[++r]);
	S.__c && S.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			S.__e(e, t.__v);
		}
	});
}
function Ce(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : ie(e) ? e.map(Ce) : e.constructor === void 0 ? F({}, e) : null;
}
function we(e, t, n, r, i, a, o, s, c) {
	var l, u, d, f, p, m, h, g = n.props || P, _ = t.props, v = t.type;
	if (v == "svg" ? i = "http://www.w3.org/2000/svg" : v == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (l = 0; l < a.length; l++) if ((p = a[l]) && "setAttribute" in p == !!v && (v ? p.localName == v : p.nodeType == 3)) {
			e = p, a[l] = null;
			break;
		}
	}
	if (e == null) {
		if (v == null) return document.createTextNode(_);
		e = document.createElementNS(i, v, _.is && _), s &&= (S.__m && S.__m(t, a), !1), a = null;
	}
	if (v == null) g === _ || s && e.data == _ || (e.data = _);
	else {
		if (a = v == "textarea" && _.defaultValue != null ? null : a && x.call(e.childNodes), !s && a != null) for (g = {}, l = 0; l < e.attributes.length; l++) g[(p = e.attributes[l]).name] = p.value;
		for (l in g) p = g[l], l == "dangerouslySetInnerHTML" ? d = p : l == "children" || l in _ || l == "value" && "defaultValue" in _ || l == "checked" && "defaultChecked" in _ || ve(e, l, null, p, i);
		for (l in _) p = _[l], l == "children" ? f = p : l == "dangerouslySetInnerHTML" ? u = p : l == "value" ? m = p : l == "checked" ? h = p : s && typeof p != "function" || g[l] === p || ve(e, l, p, g[l], i);
		if (u) s || d && (u.__html == d.__html || u.__html == e.innerHTML) || (e.innerHTML = u.__html), t.__k = [];
		else if (d && (e.innerHTML = ""), pe(t.type == "template" ? e.content : e, ie(f) ? f : [f], t, n, r, v == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && L(n, 0), s, c), a != null) for (l = a.length; l--;) ae(a[l]);
		s && v != "textarea" || (l = "value", v == "progress" && m == null ? e.removeAttribute("value") : m != null && (m !== e[l] || v == "progress" && !m || v == "option" && m != g[l]) && ve(e, l, m, g[l], i), l = "checked", h != null && h != e[l] && ve(e, l, h, g[l], i));
	}
	return e;
}
function Te(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		S.__e(e, n);
	}
}
function Ee(e, t, n) {
	var r, i;
	if (S.unmount && S.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || Te(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			S.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && Ee(r[i], t, n || typeof e.type != "function");
	n || ae(e.__e), e.__c = e.__ = e.__e = void 0;
}
function De(e, t, n) {
	return this.constructor(e, n);
}
function Oe(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), S.__ && S.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], be(t, e = (!r && n || t).__k = oe(I, null, [e]), i || P, P, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? x.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), Se(a, e, o), e.props.children = null;
}
x = ne.slice, S = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, C = 0, w = function(e) {
	return e != null && e.constructor === void 0;
}, ce.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = F({}, this.state);
	typeof e == "function" && (e = e(F({}, n), this.props)), e && F(n, e), e != null && this.__v && (t && this._sb.push(t), de(this));
}, ce.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), de(this));
}, ce.prototype.render = I, T = [], D = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, O = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, fe.__r = 0, k = Math.random().toString(8), A = "__d" + k, j = "__a" + k, ee = /(PointerCapture)$|Capture$/i, M = 0, te = ye(!1), N = ye(!0);
//#endregion
//#region src/sort-preferences.ts
function ke(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/number-setting.ts
var Ae = {
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
function je(e, t, n, r) {
	return Number.isInteger(e) && e >= t && e <= n ? e : r;
}
function Me(e, t, n) {
	let r = e.querySelector("input[type=number]"), i = e.querySelector("[role=switch]"), a = e.querySelector(".board-number-fields");
	r && (r.disabled = n, t !== null && t > 0 && (r.value = String(t))), i && (i.disabled = n, t !== null && (i.checked = t > 0)), a && t !== null && (a.hidden = t === 0);
}
function Ne(e, t, n, r, i) {
	let a = Ae[t];
	if (!a) return !1;
	let { min: o, max: s, unit: c, optional: l, fallback: u } = a, d = `peach.number.${t}`, f = je(Number(localStorage.getItem(d)), o, s, r > 0 ? r : u), p = document.createElement("div");
	p.className = "board-optional-number";
	let m = document.createElement("div");
	m.className = "board-number-fields", m.hidden = !!l && r === 0;
	let h = document.createElement("div");
	h.className = "board-number-control";
	let g = document.createElement("input");
	g.type = "number", g.className = "geist-input", g.min = String(o), g.max = String(s), g.step = "1", g.value = String(r > 0 ? r : f), g.setAttribute("aria-label", n);
	let _ = document.createElement("span");
	_.textContent = c, _.setAttribute("aria-hidden", "true");
	let v = document.createElement("small");
	v.id = `${t}-error`, v.className = "board-number-error", v.setAttribute("role", "status"), v.hidden = !0, g.setAttribute("aria-describedby", v.id), h.append(g, _), m.append(h, v), p.append(m), e.replaceChildren(p);
	let y = () => {
		g.removeAttribute("aria-invalid"), v.hidden = !0, v.textContent = "";
	}, b = () => {
		if (!g.value || !g.checkValidity()) {
			g.setAttribute("aria-invalid", "true"), v.textContent = `请输入 ${o}–${s} 的整数（${c}）`, v.hidden = !1;
			return;
		}
		y(), f = Number(g.value), localStorage.setItem(d, String(f)), i(g.value);
	};
	if (g.addEventListener("change", b), g.addEventListener("keydown", (e) => {
		e.key === "Enter" && (e.preventDefault(), b());
	}), g.addEventListener("input", () => {
		g.value && g.checkValidity() && y();
	}), l) {
		let e = document.createElement("input");
		e.type = "checkbox", e.className = "ptoggle", e.setAttribute("role", "switch"), e.setAttribute("aria-label", `启用${n}`), e.checked = r > 0, e.onchange = () => {
			y(), m.hidden = !e.checked, e.checked ? (g.value = String(f), b()) : (g.value && g.checkValidity() && (f = Number(g.value)), localStorage.setItem(d, String(f)), i("0"));
		}, p.prepend(e);
	}
	return !0;
}
//#endregion
//#region src/board-metrics.ts
var R = (e) => String(e ?? "").replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function Pe(e, t, n, r = "chart-no-axes-combined") {
	return `<span class="board-stat-label"><span class="board-stat-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><use href="#i-${/^[a-z0-9-]+$/.test(r) ? r : "database"}"/></svg></span>${R(e)}</span><b class="board-stat-value">${R(t)}</b><small class="board-stat-footer">${R(n || "当前记录")}</small>`;
}
function Fe(e, t, n) {
	if (!Number.isFinite(n) || n <= 0) return "";
	let r = Math.max(0, Math.min(n, Number.isFinite(t) ? t : 0)), i = r / n * 100;
	return `<div class="board-job-progress" role="progressbar" aria-label="${R(e)}" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${r}"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle class="board-job-track" cx="18" cy="18" r="15"/><circle class="board-job-fill" cx="18" cy="18" r="15" pathLength="100" stroke-dasharray="${i} ${100 - i}" transform="rotate(-90 18 18)"/></svg><span>${R(e)}<small>${Math.round(i)}%</small></span></div>`;
}
function Ie(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0), r = n.reduce((e, t) => e + t.score, 0);
	if (!r) return "";
	let i = 0, a = n.map((e, t) => {
		let n = e.score / r * 100, a = `<circle cx="100" cy="100" r="72" pathLength="100" fill="none" stroke="var(--chart-${t % 4})" stroke-width="22" stroke-dasharray="${n} ${100 - n}" stroke-dashoffset="${-i}"><title>${R(e.name)}：${e.score.toLocaleString()}</title></circle>`;
		return i += n, a;
	}).join("");
	return `<svg class="board-distribution" viewBox="0 0 200 200" role="img" aria-label="${R(t)}"><g transform="rotate(-90 100 100)">${a}</g><text x="100" y="100" text-anchor="middle" dominant-baseline="middle">${R(t)}</text></svg>`;
}
function Le(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0).slice().sort((e, t) => t.score - e.score).slice(0, 8);
	if (!n.length) return "";
	let r = n[0].score, i = n.map((e) => `<li><span class="board-rank-fill" style="width:${(e.score / r * 100).toFixed(2)}%"></span><span>${R(e.name)}</span><b>${e.score.toLocaleString()}</b></li>`).join("");
	return `<ol class="board-ranked-chart" aria-label="${R(t)}">${i}</ol>`;
}
function Re(e, t) {
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
		return `<text x="${n}" y="${r}" text-anchor="${n < 145 ? "end" : n > 175 ? "start" : "middle"}">${R(e.name)}</text>`;
	}).join("");
	return `<svg class="board-radar" viewBox="0 0 320 280" role="img" aria-label="${R(t)}"><title>${R(n.map((e) => `${e.name} ${e.score}`).join("，"))}</title>${s}<polygon points="${o((e) => n[e].score / r * 100)}" class="board-radar-value"/>${c}</svg>`;
}
//#endregion
//#region src/sidebar-groups.ts
var ze = (e) => e.replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function Be(e, t, n = "", r = "") {
	if (!t) return "";
	let i = `sidebar-group-${encodeURIComponent(e)}`;
	return `<section class="sec${r ? " cat-" + ze(r) : ""}" data-sidebar-group="${ze(e)}"><h3><button type="button" class="board-section-toggle" aria-expanded="true" aria-controls="${i}"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${ze(e)}</span></button>${n}</h3><div class="board-sidebar-body" id="${i}">${t}</div></section>`;
}
function Ve(e) {
	e.querySelectorAll("[data-sidebar-group]").forEach((e) => {
		if (e.dataset.sidebarWired) return;
		e.dataset.sidebarWired = "true";
		let t = e.querySelector(".board-section-toggle"), n = e.querySelector(".board-sidebar-body"), r = `peach.sidebar.group.${e.dataset.sidebarGroup}`, i = null;
		try {
			i = sessionStorage.getItem(r);
		} catch {}
		let a = (e) => {
			t.setAttribute("aria-expanded", String(e)), n.hidden = !e;
		}, o = !!n.querySelector("[aria-pressed=true]");
		a(i === null ? o || e.classList.contains("cat-src") || e.dataset.sidebarGroup === "时长" : i === "open"), t.onclick = () => {
			let e = t.getAttribute("aria-expanded") !== "true";
			a(e);
			try {
				sessionStorage.setItem(r, e ? "open" : "closed");
			} catch {}
		};
	});
}
var He = !1;
async function Ue(e, t) {
	if (He) return;
	if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
		t();
		return;
	}
	let n = e.getBoundingClientRect(), r = n.left + n.width / 2, i = n.top + n.height / 2, a = Math.hypot(Math.max(r, innerWidth - r), Math.max(i, innerHeight - i)) * 2.5, o = document.createElement("style");
	o.textContent = `::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20100%20100%22%3E%3Cdefs%3E%3Cfilter%20id%3D%22b%22%20x%3D%22-50%25%22%20y%3D%22-50%25%22%20width%3D%22200%25%22%20height%3D%22200%25%22%3E%3CfeGaussianBlur%20stdDeviation%3D%222%22%2F%3E%3C%2Ffilter%3E%3C%2Fdefs%3E%3Ccircle%20cx%3D%2250%22%20cy%3D%2250%22%20r%3D%2242%22%20fill%3D%22white%22%20filter%3D%22url(%23b)%22%2F%3E%3C%2Fsvg%3E");mask-repeat:no-repeat;animation:peach-theme-reveal 820ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${r}px ${i}px;mask-size:0px 0px}to{mask-position:${r - a / 2}px ${i - a / 2}px;mask-size:${a}px ${a}px}}`, He = !0, document.head.append(o);
	try {
		await document.startViewTransition(t).finished;
	} catch {
		t();
	} finally {
		o.remove(), He = !1;
	}
}
//#endregion
//#region src/api.ts
var We = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(o(e, t)), this.name = "ApiError", this.status = t, this.body = n;
	}
}, Ge = (e) => {
	if (!e || typeof e != "object") return "";
	let t = e;
	for (let e of [
		"message",
		"detail",
		"error"
	]) {
		let n = t[e];
		if (typeof n == "string" && n) return n;
	}
	return "";
}, z = (e) => o(e);
async function B(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new We(Ge(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function V(e, t, n = "POST", r) {
	let i = await fetch(e, {
		method: n,
		...r ? { signal: r } : {},
		headers: {
			Accept: "application/json",
			"Content-Type": "application/json"
		},
		credentials: "same-origin",
		body: JSON.stringify(t)
	}), a = null;
	try {
		a = await i.json();
	} catch {}
	if (!i.ok) throw new We(Ge(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var Ke, H, qe, Je, Ye = 0, Xe = [], U = S, Ze = U.__b, Qe = U.__r, $e = U.diffed, et = U.__c, tt = U.unmount, nt = U.__;
function rt(e, t) {
	U.__h && U.__h(H, e, Ye || t), Ye = 0;
	var n = H.__H || (H.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function W(e) {
	return Ye = 1, it(ft, e);
}
function it(e, t, n) {
	var r = rt(Ke++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : ft(void 0, t), function(e) {
		var t = r.__N ? r.__N[0] : r.__[0], n = r.t(t, e);
		t !== n && (r.__N = [n, r.__[1]], r.__c.setState({}));
	}], r.__c = H, !H.__f)) {
		var i = function(e, t, n) {
			if (!r.__c.__H) return !0;
			var i = !1, o = r.__c.props !== e;
			if (r.__c.__H.__.some(function(e) {
				if (e.__N) {
					i = !0;
					var t = e.__[0];
					e.__ = e.__N, e.__N = void 0, t !== e.__[0] && (o = !0);
				}
			}), a) {
				var s = a.call(this, e, t, n);
				return i ? s || o : s;
			}
			return !i || o;
		};
		H.__f = !0;
		var a = H.shouldComponentUpdate, o = H.componentWillUpdate;
		H.componentWillUpdate = function(e, t, n) {
			if (this.__e) {
				var r = a;
				a = void 0, i(e, t, n), a = r;
			}
			o && o.call(this, e, t, n);
		}, H.shouldComponentUpdate = i;
	}
	return r.__N || r.__;
}
function G(e, t) {
	var n = rt(Ke++, 3);
	!U.__s && dt(n.__H, t) && (n.__ = e, n.u = t, H.__H.__h.push(n));
}
function K(e, t) {
	var n = rt(Ke++, 4);
	!U.__s && dt(n.__H, t) && (n.__ = e, n.u = t, H.__h.push(n));
}
function q(e) {
	return Ye = 5, at(function() {
		return { current: e };
	}, []);
}
function at(e, t) {
	var n = rt(Ke++, 7);
	return dt(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function ot() {
	for (var e; e = Xe.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(lt), t.__h.some(ut), t.__h = [];
		} catch (n) {
			t.__h = [], U.__e(n, e.__v);
		}
	}
}
U.__b = function(e) {
	H = null, Ze && Ze(e);
}, U.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), nt && nt(e, t);
}, U.__r = function(e) {
	Qe && Qe(e), Ke = 0;
	var t = (H = e.__c).__H;
	t && (qe === H ? (t.__h = [], H.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(lt), t.__h.some(ut), t.__h = [], Ke = 0)), qe = H;
}, U.diffed = function(e) {
	$e && $e(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Xe.push(t) !== 1 && Je === U.requestAnimationFrame || ((Je = U.requestAnimationFrame) || ct)(ot)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), qe = H = null;
}, U.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(lt), e.__h = e.__h.filter(function(e) {
				return !e.__ || ut(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], U.__e(n, e.__v);
		}
	}), et && et(e, t);
}, U.unmount = function(e) {
	tt && tt(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			lt(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && U.__e(t, n.__v));
};
var st = typeof requestAnimationFrame == "function";
function ct(e) {
	var t, n = function() {
		clearTimeout(r), st && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	st && (t = requestAnimationFrame(n));
}
function lt(e) {
	var t = H, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), H = t;
}
function ut(e) {
	var t = H;
	e.__c = e.__(), H = t;
}
function dt(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function ft(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var pt = 0;
Array.isArray;
function J(e, t, n, r, i, a) {
	t ||= {};
	var o, s, c = t;
	if ("ref" in c) for (s in c = {}, t) s == "ref" ? o = t[s] : c[s] = t[s];
	var l = {
		type: e,
		props: c,
		key: n,
		ref: o,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: --pt,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (o = e.defaultProps)) for (s in o) c[s] === void 0 && (c[s] = o[s]);
	return S.vnode && S.vnode(l), l;
}
//#endregion
//#region src/islands/access-settings.tsx
function mt({ id: e, label: t, value: n, onInput: r, error: i, help: a, current: o = !1, disabled: s = !1 }) {
	return /* @__PURE__ */ J("div", {
		class: "configfield",
		children: [
			/* @__PURE__ */ J("label", {
				for: e,
				children: t
			}),
			/* @__PURE__ */ J("input", {
				id: e,
				class: "geist-input",
				type: "password",
				autoComplete: o ? "current-password" : "new-password",
				maxLength: 256,
				value: n,
				onInput: (e) => r(e.currentTarget.value),
				required: !s,
				disabled: s,
				"aria-invalid": !!i,
				"aria-describedby": i || a ? `${e}-hint` : void 0
			}),
			i || a ? /* @__PURE__ */ J("p", {
				id: `${e}-hint`,
				class: i ? "configbad" : "confighelp",
				role: i ? "alert" : void 0,
				children: i || a
			}) : null
		]
	});
}
function ht({ initial: e, receipt: t }) {
	let [n, r] = W(e), [i, a] = W(""), [o, s] = W(""), [c, l] = W(""), [u, f] = W(!1), [m, h] = W(""), [g, _] = W({}), y = q(null), b = q(!1), x = q(null);
	return /* @__PURE__ */ J("form", {
		class: "configfieldset",
		"data-fieldset-type": u ? "warning" : void 0,
		onSubmit: async (e) => {
			if (e.preventDefault(), b.current) return;
			h("");
			let d = {};
			if (n.mode === "password" && !i && (d.current_password = "请输入当前访问密码"), u || ((o.length < 8 || o.length > 256) && (d.password = "访问密码需为 8–256 个字符"), o !== c && (d.confirmation = "两次输入的密码不一致")), _(d), Object.keys(d).length) {
				requestAnimationFrame(() => y.current?.querySelector("[aria-invalid=\"true\"]")?.focus());
				return;
			}
			b.current = !0, v(x.current, !0);
			try {
				let e = await V("/api/configuration/access", {
					revision: n.revision,
					action: u ? "disable" : "set",
					confirm_disable: u,
					current_password: i,
					password: u ? "" : o,
					confirmation: u ? "" : c
				});
				r(e), a(""), s(""), l(""), f(!1), _({}), t(e.mode === "open" ? "已关闭访问密码" : "已保存访问密码");
			} catch (e) {
				let t = e instanceof We ? e.body : null, n = t?.errors || t?.detail?.errors;
				n ? _(n) : h(z(e));
			} finally {
				b.current = !1, v(x.current, !1);
			}
		},
		"aria-labelledby": "accessTitle",
		noValidate: !0,
		ref: y,
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: d("accessTitle", "访问密码") } }), /* @__PURE__ */ J("p", {
						class: "confighelp",
						children: n.mode === "open" ? "未设置密码，能连接到 Peach 的设备可直接访问。" : n.mode === "legacy" ? "当前使用系统生成的访问口令。你可以设置自己的密码，或关闭登录要求。" : n.mode === "locked" ? "访问设置无法读取，请在本机检查配置文件。" : "已设置密码。新设备需要登录，保持登录时间在登录页选择。"
					})]
				}),
				n.mode === "password" || n.mode === "legacy" ? /* @__PURE__ */ J("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ J("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ J("input", {
							type: "checkbox",
							checked: u,
							onChange: (e) => f(e.currentTarget.checked)
						}), /* @__PURE__ */ J("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ J("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ J("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ J("span", { children: "关闭访问密码，允许能连接到 Peach 的设备直接访问" })]
				}) : null,
				n.mode === "password" ? /* @__PURE__ */ J(mt, {
					id: "access-current",
					label: "当前访问密码",
					value: i,
					onInput: a,
					error: g.current_password,
					current: !0
				}) : null,
				n.mode === "locked" ? null : /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J(mt, {
					id: "access-password",
					label: n.mode === "password" ? "新访问密码" : "设置访问密码",
					value: o,
					onInput: s,
					disabled: u,
					error: u ? void 0 : g.password,
					help: u ? "关闭访问密码时无需填写。" : "至少 8 个字符。保存后其他设备需要重新登录。"
				}), /* @__PURE__ */ J(mt, {
					id: "access-confirm",
					label: "确认访问密码",
					value: c,
					onInput: l,
					disabled: u,
					error: u ? void 0 : g.confirmation
				})] }),
				u && /* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: p("保存后，能连接到 Peach 的设备将直接访问馆藏。", {
					variant: "warning",
					label: "访问范围"
				}) } }),
				m ? /* @__PURE__ */ J("p", {
					class: "configbad",
					role: "alert",
					children: m
				}) : null
			]
		}), n.mode === "locked" ? null : /* @__PURE__ */ J("div", {
			class: "geist-fieldset-footer",
			children: [/* @__PURE__ */ J("p", { children: "保存后立即生效。" }), /* @__PURE__ */ J("button", {
				class: "geist-button primary",
				type: "submit",
				ref: x,
				children: "保存配置"
			})]
		})]
	});
}
//#endregion
//#region src/islands/release-updates.tsx
var gt = /* @__PURE__ */ new Set([
	"downloading",
	"verifying",
	"extracting",
	"preparing",
	"restarting",
	"installing"
]);
function _t({ initial: e, initialJob: t }) {
	let [n, r] = W(e), [i, a] = W(t || {
		state: "idle",
		progress: 0
	}), [o, s] = W(""), c = q(null), u = q(!0), f = q(!1), h = q(null);
	G(() => {
		v(h.current, gt.has(i.state));
	}, [i.state]), G(() => () => {
		u.current = !1, c.current?.abort();
	}, []);
	let g = async () => {
		let e = await V("/api/configuration/update-restart", {});
		u.current && a(e);
	};
	G(() => {
		i.state !== "ready" || f.current || (f.current = !0, l({
			title: "更新已准备好",
			body: `Peach ${i.version || ""} 将在重启后安装。`,
			confirmLabel: "立即重启",
			cancelLabel: "稍后",
			onConfirm: g
		}));
	}, [i.state]), G(() => {
		if (!gt.has(i.state)) return;
		let e = new AbortController(), t, n = 0, o = async () => {
			try {
				let t = await B("/api/configuration/update-status", e.signal);
				e.signal.aborted || (a(t), n = 0, t.state === "complete" && r((e) => ({
					...e,
					current_version: t.version || e.current_version,
					state: "current",
					message: "已是最新测试版。"
				})));
			} catch {
				++n >= 120 && !e.signal.aborted && s("尚未连接到 Peach，请检查托盘后刷新页面。");
			}
			!e.signal.aborted && n < 120 && (t = setTimeout(o, 1e3));
		};
		return t = setTimeout(o, 1e3), () => {
			e.abort(), clearTimeout(t);
		};
	}, [i.state]);
	let _ = async (e) => {
		if (c.current || gt.has(i.state)) return;
		let t = new AbortController();
		c.current = t, f.current = !1, s(""), v(e, !0);
		try {
			let e = await V("/api/configuration/update", {}, "POST", t.signal);
			t.signal.aborted || a(e);
		} catch (e) {
			t.signal.aborted || s(z(e));
		} finally {
			c.current = null, v(e, !1);
		}
	}, y = async (t) => {
		if (c.current) return;
		let n = new AbortController();
		c.current = n, v(t, !0), s("");
		try {
			let e = await B("/api/configuration/updates", n.signal);
			n.signal.aborted || r(e);
		} catch (t) {
			n.signal.aborted || (r({
				...e,
				state: "error"
			}), s(z(t)));
		} finally {
			c.current = null, v(t, !1);
		}
	};
	return /* @__PURE__ */ J("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configUpdatesTitle",
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: d("configUpdatesTitle", "检查更新") } }),
				/* @__PURE__ */ J("dl", {
					class: "configfacts",
					children: [
						/* @__PURE__ */ J("dt", { children: "当前版本" }),
						/* @__PURE__ */ J("dd", { children: n.current_version }),
						/* @__PURE__ */ J("dt", { children: "安装方式" }),
						/* @__PURE__ */ J("dd", { children: n.installation }),
						/* @__PURE__ */ J("dt", { children: "更新通道" }),
						/* @__PURE__ */ J("dd", { children: n.channel }),
						/* @__PURE__ */ J("dt", { children: "最新版本" }),
						/* @__PURE__ */ J("dd", { children: n.latest_version || (n.state === "unchecked" ? "尚未检查" : "未取得") })
					]
				}),
				n.state === "available" && !o ? /* @__PURE__ */ J("div", {
					role: "status",
					dangerouslySetInnerHTML: { __html: p(n.message, { label: "有可用更新" }) }
				}) : /* @__PURE__ */ J("p", {
					class: o || n.state === "error" ? "configbad" : "confighelp",
					role: o || n.state === "error" ? "alert" : "status",
					children: o || n.message
				}),
				i.state === "idle" ? null : /* @__PURE__ */ J("div", {
					"aria-live": "polite",
					children: [/* @__PURE__ */ J("p", {
						class: i.state === "error" ? "configbad" : "confighelp",
						children: i.message
					}), i.state === "error" ? null : /* @__PURE__ */ J(I, { children: [
						/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: m("更新准备进度：下载、校验、解压、准备安装", i.progress, 100, { stops: [
							{
								value: 65,
								label: "下载结束"
							},
							{
								value: 67,
								label: "校验结束"
							},
							{
								value: 90,
								label: "准备安装"
							}
						] }) } }),
						/* @__PURE__ */ J("p", {
							class: "confighelp",
							children: ["下载 → 校验 → 解压 → 准备安装 · ", i.message]
						}),
						/* @__PURE__ */ J("p", {
							class: "confighelp",
							children: i.state === "downloading" && i.total ? `${((i.downloaded || 0) / 1048576).toFixed(1)} / ${(i.total / 1048576).toFixed(1)} MB` : `${i.progress}%`
						})
					] })]
				})
			]
		}), /* @__PURE__ */ J("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [
				/* @__PURE__ */ J("a", {
					class: "geist-button externallink",
					href: n.release_url,
					target: "_blank",
					rel: "noreferrer",
					children: ["查看发布页", /* @__PURE__ */ J("svg", {
						class: "externalmark",
						viewBox: "0 0 24 24",
						"aria-hidden": "true",
						children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
					})]
				}),
				i.state === "ready" ? /* @__PURE__ */ J("button", {
					type: "button",
					class: "geist-button primary",
					onClick: () => {
						l({
							title: "更新已准备好",
							body: `Peach ${i.version || ""} 将在重启后安装。`,
							confirmLabel: "立即重启",
							cancelLabel: "稍后",
							onConfirm: g
						});
					},
					children: "重启安装"
				}) : null,
				n.state === "available" && n.installation === "独立测试包" && i.state !== "ready" ? /* @__PURE__ */ J("button", {
					ref: h,
					type: "button",
					class: "geist-button primary",
					onClick: (e) => _(e.currentTarget),
					children: "下载并安装"
				}) : null,
				/* @__PURE__ */ J("button", {
					type: "button",
					class: "geist-button",
					disabled: gt.has(i.state),
					onClick: (e) => y(e.currentTarget),
					children: "检查更新"
				})
			]
		})]
	});
}
//#endregion
//#region src/islands/peach-proxy.tsx
function vt({ initial: e, receipt: t }) {
	let [n, r] = W(e), [i, a] = W(e.mode), [o, s] = W(""), [c, l] = W(""), u = q(!1), f = q(null), p = q(null), m = q(new AbortController());
	G(() => () => m.current.abort(), []), K(() => {
		let t = f.current;
		t.innerHTML = g([
			["environment", "系统代理"],
			["direct", "直连"],
			["proxy", "自定义"]
		], e.mode, {
			label: "Peach 代理",
			className: "configselect",
			attr: "data-fixed-width"
		});
		let n = b(t.firstElementChild), r = () => a(n.value);
		return n.addEventListener("change", r), () => {
			n.removeEventListener("change", r), t.replaceChildren();
		};
	}, []);
	async function h() {
		if (!u.current) {
			u.current = !0, v(p.current, !0), l("");
			try {
				let e = await V("/api/configuration/peach-proxy", {
					mode: i,
					proxy: o
				}, "POST", m.current.signal);
				m.current.signal.aborted || (r(e), s(""), t("已保存 Peach 代理"));
			} catch (e) {
				m.current.signal.aborted || l(z(e));
			} finally {
				u.current = !1, v(p.current, !1);
			}
		}
	}
	return /* @__PURE__ */ J("form", {
		id: "peachProxy",
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), h();
		},
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: d("peachProxyTitle", "Peach 代理") } }), /* @__PURE__ */ J("p", {
						class: "confighelp",
						children: "采集来源选择“Peach 代理”时共用此设置。"
					})]
				}),
				/* @__PURE__ */ J("div", { ref: f }),
				i === "proxy" && /* @__PURE__ */ J("div", {
					class: "configfield",
					children: [/* @__PURE__ */ J("label", {
						htmlFor: "peachProxyAddress",
						children: "代理地址"
					}), /* @__PURE__ */ J("input", {
						id: "peachProxyAddress",
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: o,
						placeholder: n.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						onInput: (e) => s(e.currentTarget.value)
					})]
				}),
				n.needs_selection && /* @__PURE__ */ J("p", {
					class: "configbad",
					children: "已有来源的代理地址不同，请选择公共连接方式。"
				}),
				c && /* @__PURE__ */ J("p", {
					class: "configbad",
					role: "alert",
					children: c
				})
			]
		}), /* @__PURE__ */ J("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ J("button", {
				ref: p,
				class: "geist-button primary",
				type: "submit",
				children: "保存代理"
			})
		})]
	});
}
//#endregion
//#region src/islands/desktop-settings.tsx
function yt({ label: e, checked: t, disabled: n, change: r }) {
	return /* @__PURE__ */ J("label", {
		class: "configcheck",
		children: [/* @__PURE__ */ J("span", {
			class: "pcheck",
			children: [/* @__PURE__ */ J("input", {
				type: "checkbox",
				checked: t,
				disabled: n,
				onChange: (e) => r(e.currentTarget.checked)
			}), /* @__PURE__ */ J("span", {
				"aria-hidden": "true",
				children: /* @__PURE__ */ J("svg", {
					viewBox: "0 0 24 24",
					children: /* @__PURE__ */ J("use", { href: "#i-check" })
				})
			})]
		}), /* @__PURE__ */ J("span", { children: e })]
	});
}
function bt({ label: e, checked: t, disabled: n, change: r }) {
	return /* @__PURE__ */ J("label", {
		class: "configtoggle",
		children: [/* @__PURE__ */ J("span", { children: e }), /* @__PURE__ */ J("input", {
			class: "ptoggle",
			type: "checkbox",
			role: "switch",
			checked: t,
			disabled: n,
			onChange: (e) => r(e.currentTarget.checked)
		})]
	});
}
function xt({ startup: e, receipt: t }) {
	let [n, r] = W(e.enabled), [i, a] = W(e.silent), [o, s] = W(e.desktop), [c, l] = W(""), u = q(!1), f = q(null), p = e.available && !e.desktop_message;
	async function m() {
		if (!u.current) {
			u.current = !0, v(f.current, !0), l("");
			try {
				await V("/api/configuration/startup", {
					enabled: n,
					silent: i,
					desktop: o
				}), t("已保存开机自启");
			} catch (e) {
				l(z(e));
			} finally {
				u.current = !1, v(f.current, !1);
			}
		}
	}
	return /* @__PURE__ */ J("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), m();
		},
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: d("startupTitle", "开机自启") } }),
				/* @__PURE__ */ J("div", {
					class: "configoptions",
					role: "group",
					"aria-labelledby": "startupTitle",
					children: [
						/* @__PURE__ */ J(bt, {
							label: "开机后启动 Peach",
							checked: n,
							disabled: !e.available,
							change: r
						}),
						/* @__PURE__ */ J("div", {
							class: "configoption",
							children: [/* @__PURE__ */ J(bt, {
								label: "静默启动",
								checked: i,
								disabled: !e.available || !n,
								change: a
							}), /* @__PURE__ */ J("p", {
								class: "confighelp",
								children: "静默启动仅显示托盘，开机后启动 Peach 打开时生效。"
							})]
						}),
						/* @__PURE__ */ J("div", {
							class: "configoption",
							children: [/* @__PURE__ */ J(bt, {
								label: "在桌面创建快捷方式",
								checked: o,
								disabled: !p,
								change: s
							}), /* @__PURE__ */ J("p", {
								class: "confighelp",
								children: e.desktop_message || "双击图标打开 Peach 网页；卸载时一并移除。"
							})]
						})
					]
				}),
				e.message && /* @__PURE__ */ J("p", {
					class: "confighelp",
					children: e.message
				}),
				c && /* @__PURE__ */ J("p", {
					class: "configbad",
					role: "alert",
					children: c
				})
			]
		}), /* @__PURE__ */ J("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ J("button", {
				ref: f,
				type: "submit",
				class: "geist-button primary",
				disabled: !e.available,
				children: "保存配置"
			})
		})]
	});
}
function St({ data: e }) {
	let t = q(null);
	return K(() => {
		let n = t.current, r = document.createElement("details");
		r.className = "configdirectories";
		let i = document.createElement("summary");
		i.innerHTML = a("chevron-right") + "<span>数据目录</span>", r.append(i);
		for (let t of [.../* @__PURE__ */ new Set([e.data_root, ...e.directories])]) {
			let e = document.createElement("p");
			e.className = "confighelp", e.textContent = t, r.append(e);
		}
		return n.replaceChildren(r), y(n, "details", "uninstall-data"), () => n.replaceChildren();
	}, [e]), /* @__PURE__ */ J("div", { ref: t });
}
function Ct({ uninstall: e }) {
	let [t, n] = W(!1), [r, i] = W("");
	async function a() {
		await l({
			title: "卸载 Peach",
			danger: !0,
			body: t ? "将退出 Peach，移除程序、开机自启、桌面图标、设置、本地数据库、观看记录、凭据和缓存。原始媒体文件保留。" : "将退出 Peach 并移除程序、开机自启和桌面图标。设置、本地数据库、观看记录与缓存保留。",
			confirmLabel: "卸载 Peach",
			onConfirm: async () => {
				let e = await V("/api/configuration/uninstall", {
					delete_data: t,
					confirmation: "卸载 Peach"
				});
				i(e.message);
			}
		});
	}
	return /* @__PURE__ */ J("section", {
		id: "uninstallPeach",
		class: "configfieldset configdanger",
		"data-geist-fieldset": !0,
		"data-fieldset-type": "error",
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: d("uninstallTitle", "卸载 Peach") } }), e.available && /* @__PURE__ */ J("p", {
						class: "confighelp",
						children: "卸载会退出 Peach、移除程序、开机自启和桌面图标。原始媒体文件保留。"
					})]
				}),
				/* @__PURE__ */ J(yt, {
					label: "完全卸载：同时删除设置、本地数据库、观看记录、凭据和缓存",
					checked: t,
					disabled: !e.full_available || !!r,
					change: n
				}),
				/* @__PURE__ */ J(St, { data: e }),
				e.message && /* @__PURE__ */ J("p", {
					class: "confighelp",
					children: e.message
				}),
				r && /* @__PURE__ */ J("p", {
					class: "confighelp",
					role: "status",
					children: r
				})
			]
		}), /* @__PURE__ */ J("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ J("button", {
				type: "button",
				class: "geist-button danger",
				disabled: !e.available || !!r,
				onClick: () => void a(),
				children: "卸载 Peach"
			})
		})]
	});
}
//#endregion
//#region src/islands/clouddrive-guide.tsx
var wt = [
	{
		name: "机械硬盘，或内存 8 GB 以内",
		cache: "10–20 GiB",
		read: "256 / 128 KB",
		task: "1 个"
	},
	{
		name: "SATA SSD，内存 8–16 GB",
		cache: "20–50 GiB",
		read: "256 / 128 KB",
		task: "1–2 个"
	},
	{
		name: "NVMe SSD，内存 16 GB 以上",
		cache: "50–100 GiB",
		read: "256 / 128 KB",
		task: "2 个起步"
	}
];
function Tt() {
	let e = q(null);
	return K(() => {
		e.current && y(e.current, "details", "clouddrive-guide");
	}, []), /* @__PURE__ */ J("div", {
		ref: e,
		class: "cloudguide",
		children: [/* @__PURE__ */ J("p", {
			class: "confighelp",
			children: ["先在 CloudDrive 登录网盘并挂载，开启「启动时自动挂载」。", /* @__PURE__ */ J("a", {
				class: "externallink",
				href: "https://www.clouddrive2.com/help.html",
				target: "_blank",
				rel: "noreferrer",
				children: ["挂载帮助", /* @__PURE__ */ J("svg", {
					class: "externalmark",
					viewBox: "0 0 24 24",
					"aria-hidden": "true",
					children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
				})]
			})]
		}), /* @__PURE__ */ J("details", { children: [
			/* @__PURE__ */ J("summary", { children: [/* @__PURE__ */ J("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true",
				children: /* @__PURE__ */ J("use", { href: "#i-chevron-right" })
			}), "CloudDrive 速度与缓存建议"] }),
			/* @__PURE__ */ J("p", {
				class: "confighelp",
				children: "看缓存放在哪块硬盘上，照那一行填。表里是起步值，先保证播放不卡，再拿同一个视频比较打开速度、拖动和流量；填得越大不一定越快。"
			}),
			/* @__PURE__ */ J("div", {
				class: "cloudguide-tablewrap",
				children: /* @__PURE__ */ J("table", {
					class: "cloudguide-table",
					children: [/* @__PURE__ */ J("thead", { children: /* @__PURE__ */ J("tr", { children: [
						/* @__PURE__ */ J("th", {
							scope: "col",
							children: "缓存所在硬盘"
						}),
						/* @__PURE__ */ J("th", {
							scope: "col",
							children: "缓存上限"
						}),
						/* @__PURE__ */ J("th", {
							scope: "col",
							children: "读取长度（默认 / 最小）"
						}),
						/* @__PURE__ */ J("th", {
							scope: "col",
							children: "同时处理视频"
						})
					] }) }), /* @__PURE__ */ J("tbody", { children: wt.map((e) => /* @__PURE__ */ J("tr", { children: [
						/* @__PURE__ */ J("th", {
							scope: "row",
							children: e.name
						}),
						/* @__PURE__ */ J("td", { children: e.cache }),
						/* @__PURE__ */ J("td", { children: e.read }),
						/* @__PURE__ */ J("td", { children: e.task })
					] }, e.name)) })]
				})
			}),
			/* @__PURE__ */ J("ul", {
				class: "cloudguide-notes",
				children: [
					/* @__PURE__ */ J("li", { children: "缓存上限和清理方式填在 CloudDrive「设置」里，清理方式选 LRU。上限不要填 0，系统盘至少留 40 GiB。" }),
					/* @__PURE__ */ J("li", { children: "读取长度和下载线程填在每个网盘各自的下载设置里，线程都从 2 开始。看高码率视频还是缓冲就试 512 / 256 KB，打开速度、拖动和流量都没改善就调回去。" }),
					/* @__PURE__ */ J("li", { children: "Buffer Cache 占内存，磁盘缓存和文件夹缓存占硬盘，三处是分开的设置，改一个管不住另外两个。" }),
					/* @__PURE__ */ J("li", { children: "填完重新打开 CloudDrive 的设置页确认存住了，再看硬盘实际少了多少。播放期间先暂停批量抽帧、关掉不用的播放页。" })
				]
			}),
			/* @__PURE__ */ J("p", {
				class: "confighelp",
				children: [
					"三处缓存分别管什么、码率和速度怎么换算、线程上限与直链代理怎么取舍，以及这些起步值的来源，都在",
					/* @__PURE__ */ J("a", {
						class: "externallink",
						href: "https://github.com/longmeidao/peach/blob/master/docs/CLOUDDRIVE.md",
						target: "_blank",
						rel: "noreferrer",
						children: ["CloudDrive 配置与调优", /* @__PURE__ */ J("svg", {
							class: "externalmark",
							viewBox: "0 0 24 24",
							"aria-hidden": "true",
							children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
						})]
					}),
					"。"
				]
			})
		] })]
	});
}
//#endregion
//#region src/islands/configuration.tsx
var Et = "/api/configuration", Dt = "/api/pick-folder", Ot = 8e3, kt = (e, t) => B(Et, t), At = ({ html: e, class: t }) => /* @__PURE__ */ J("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), jt = (e) => !(e instanceof We) || e.status !== 400 ? null : e.body?.errors ?? null;
function Mt({ facts: e }) {
	return /* @__PURE__ */ J("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ J(At, { html: d("configFactsTitle", "运行信息") }), /* @__PURE__ */ J("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J("dt", { children: e.term }), /* @__PURE__ */ J("dd", { children: [e.value, e.download_url ? /* @__PURE__ */ J("span", {
					class: "confighelp",
					children: [" ", /* @__PURE__ */ J("a", {
						class: "externallink",
						href: e.download_url,
						target: "_blank",
						rel: "noreferrer",
						children: [e.download_label, /* @__PURE__ */ J("svg", {
							class: "externalmark",
							viewBox: "0 0 24 24",
							"aria-hidden": "true",
							children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
						})]
					})]
				}) : null] })] }))
			})]
		})
	});
}
function Nt({ data: e }) {
	let [t, n] = W(e.media_sources), [r, i] = W(""), a = q(null);
	G(() => () => a.current?.abort(), []);
	let o = async (e) => {
		if (a.current) return;
		let t = new AbortController();
		a.current = t, v(e, !0), i("");
		try {
			let e = await B(Et, t.signal);
			t.signal.aborted || n(e.media_sources);
		} catch (e) {
			t.signal.aborted || i(z(e));
		} finally {
			a.current = null, v(e, !1);
		}
	};
	return t ? /* @__PURE__ */ J("section", {
		class: "configfieldset",
		"aria-labelledby": "configMountsTitle",
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J(At, { html: d("configMountsTitle", "挂载状态") }),
				/* @__PURE__ */ J("dl", {
					class: "configfacts",
					children: t.map((e) => /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J("dt", { children: [/* @__PURE__ */ J("span", {
						"aria-hidden": "true",
						dangerouslySetInnerHTML: { __html: _(s[e.location]) }
					}), {
						local: "本地磁盘",
						115: "CloudDrive · 115",
						pikpak: "CloudDrive · PikPak"
					}[e.location] || e.location] }), /* @__PURE__ */ J("dd", { children: [
						e.path || "未配置挂载点",
						" ",
						/* @__PURE__ */ J("span", {
							class: `configstatus ${e.online === !0 ? "online" : e.online === !1 ? "offline" : "unknown"}`,
							children: e.online === !0 ? "在线" : e.online === !1 ? "离线" : "未检测"
						})
					] })] }))
				}),
				r ? /* @__PURE__ */ J("p", {
					class: "configbad",
					role: "alert",
					children: r
				}) : null
			]
		}), /* @__PURE__ */ J("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ J("button", {
				type: "button",
				class: "geist-button",
				onClick: (e) => o(e.currentTarget),
				children: "刷新挂载状态"
			})
		})]
	}) : null;
}
function Pt({ value: e, label: t, onChange: n }) {
	let r = q(null), i = q(null), a = q(n);
	return a.current = n, K(() => {
		let n = r.current;
		n.innerHTML = g([
			["local", "本地磁盘"],
			["115", "CloudDrive · 115"],
			["pikpak", "CloudDrive · PikPak"]
		].map(([e, t]) => [
			e,
			t,
			s[e]
		]), e, { label: t });
		let o = b(n.firstElementChild);
		i.current = o;
		let c = () => a.current(o.value);
		return o.addEventListener("change", c), () => {
			i.current = null, o.disabled = !0, o.removeEventListener("change", c), n.replaceChildren();
		};
	}, [t]), K(() => {
		i.current && (i.current.value = e);
	}, [e]), /* @__PURE__ */ J("div", {
		ref: r,
		class: "configsourcecontrol"
	});
}
function Ft({ data: e, receipt: t }) {
	let n = e.media_sources?.filter((e) => [
		"local",
		"115",
		"pikpak"
	].includes(e.location)), [r, i] = W(n?.length ? n.map((e) => e.path) : e.media_dirs.length ? e.media_dirs : [""]), [a, o] = W(n?.map((e) => e.location) ?? []), [s, c] = W(n?.map((e) => e.root) ?? []), [l, u] = W(n?.map((e) => e.library || "") ?? []), [f, m] = W(String(e.port)), [h, g] = W(!1), [_, y] = W([]), [b, x] = W(""), [S, C] = W(""), [w, T] = W(null), [E, D] = W(null), O = q(!1), k = q(e.revision), A = q([]), j = q(null);
	K(() => {
		E !== null && (A.current[E]?.focus(), D(null));
	}, [E]), G(() => {
		if (!w) return;
		let e = setTimeout(() => location.assign(w.url), Ot);
		return () => clearTimeout(e);
	}, [w]);
	let ee = (e, t) => {
		i((n) => n.map((n, r) => r === e ? t : n));
	}, M = () => {
		D(r.length), i((e) => [...e, ""]);
	}, te = (e) => {
		o((t) => t.filter((t, n) => n !== e)), c((t) => t.filter((t, n) => n !== e)), u((t) => t.filter((t, n) => n !== e)), i((t) => t.filter((t, n) => n !== e)), y((t) => t.filter((t, n) => n !== e));
	}, N = (e, t) => {
		y((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, P = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			v(t, !0);
			try {
				let { path: t } = await V(Dt, { initial: r[e] ?? "" });
				t && (ee(e, t), N(e, ""));
			} catch (t) {
				N(e, z(t));
			} finally {
				v(t, !1);
			}
		}
	};
	return w ? /* @__PURE__ */ J("div", {
		class: "configsaved",
		role: "status",
		children: /* @__PURE__ */ J("div", {
			class: "geist-note geist-note-success",
			role: "note",
			children: [/* @__PURE__ */ J("svg", {
				"aria-hidden": "true",
				viewBox: "0 0 24 24",
				children: /* @__PURE__ */ J("use", { href: "#i-check" })
			}), /* @__PURE__ */ J("p", { children: /* @__PURE__ */ J("span", { children: [
				"配置已保存，Peach 正在重新启动。稍后自动跳转，或点击",
				/* @__PURE__ */ J("a", {
					href: w.url,
					children: "进入馆藏"
				}),
				"。"
			] }) })]
		})
	}) : /* @__PURE__ */ J("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configTitle",
		onSubmit: async (n) => {
			if (n.preventDefault(), !O.current) {
				O.current = !0, v(j.current, !0), C("");
				try {
					let n = await V(Et, {
						revision: k.current,
						media_dirs: r,
						...e.media_sources ? { media_sources: r.map((e, t) => ({
							path: e,
							location: a[t] || "local",
							root: s[t] || "",
							library: l[t] || ""
						})) } : {},
						port: f,
						scan_now: h
					});
					k.current = n.revision, y([]), x(""), t("已保存配置"), T(n);
				} catch (e) {
					let t = jt(e);
					t ? (y(t.media_dirs ?? []), x(t.port ?? "")) : (y([]), x(""), C(z(e)));
				} finally {
					O.current = !1, v(j.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J(At, { html: d("configTitle", "这台电脑") }),
				/* @__PURE__ */ J("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ J("span", {
							class: "configlabel",
							id: "configDirsLabel",
							children: "媒体文件夹"
						}),
						/* @__PURE__ */ J("div", {
							class: "configdirs",
							role: "group",
							"aria-labelledby": "configDirsLabel",
							children: r.map((t, n) => /* @__PURE__ */ J("div", {
								class: "configdir",
								children: [
									/* @__PURE__ */ J("span", {
										class: "configpathlabel",
										children: ["本机文件夹 ", n + 1]
									}),
									/* @__PURE__ */ J("input", {
										class: "geist-input",
										type: "text",
										value: t,
										"aria-label": `媒体文件夹 ${n + 1}`,
										"aria-invalid": _[n] ? "true" : void 0,
										onInput: (e) => ee(n, e.currentTarget.value),
										ref: (e) => {
											A.current[n] = e;
										}
									}),
									/* @__PURE__ */ J("button", {
										type: "button",
										class: "geist-button configpick",
										"aria-label": "选择文件夹",
										onClick: (e) => P(n, e.currentTarget),
										children: /* @__PURE__ */ J("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ J("use", { href: "#i-folder-search" })
										})
									}),
									r.length > 1 ? /* @__PURE__ */ J("button", {
										type: "button",
										class: "geist-button configrm danger",
										"aria-label": "移除这个文件夹",
										onClick: () => te(n),
										children: /* @__PURE__ */ J("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ J("use", { href: "#i-x" })
										})
									}) : null,
									/* @__PURE__ */ J("div", {
										class: "configsource",
										children: [
											/* @__PURE__ */ J("label", { children: ["媒体库", /* @__PURE__ */ J("input", {
												class: "geist-input",
												"aria-label": `媒体库 ${n + 1}`,
												maxLength: 80,
												value: l[n] || "",
												placeholder: "同名文件夹归入同一个媒体库",
												onInput: (e) => {
													let t = [...l];
													t[n] = e.currentTarget.value, u(t);
												}
											})] }),
											/* @__PURE__ */ J("div", {
												class: "configsourcelabel",
												children: ["媒体来源", /* @__PURE__ */ J(Pt, {
													label: `媒体来源 ${n + 1}`,
													value: a[n] || "local",
													onChange: (e) => {
														let t = [...a];
														t[n] = e, o(t);
													}
												})]
											}),
											e.windows === !1 ? /* @__PURE__ */ J("label", { children: ["Windows 中的对应路径", /* @__PURE__ */ J("input", {
												class: "geist-input",
												"aria-label": `Windows 中的对应路径 ${n + 1}`,
												value: s[n] || "",
												placeholder: "例如 B:\\\\",
												onInput: (e) => {
													let t = [...s];
													t[n] = e.currentTarget.value, c(t);
												}
											})] }) : null
										]
									}),
									_[n] ? /* @__PURE__ */ J("p", {
										class: "configbad",
										role: "alert",
										children: _[n]
									}) : null
								]
							}, n))
						}),
						/* @__PURE__ */ J("button", {
							type: "button",
							class: "geist-button configadd",
							onClick: M,
							children: "添加文件夹"
						}),
						a.some((e) => e === "115" || e === "pikpak") ? /* @__PURE__ */ J(Tt, {}) : null,
						a.some((e) => e === "115" || e === "pikpak") ? e.mount_dependencies?.filter((e) => !e.available).map((e) => /* @__PURE__ */ J("p", {
							class: "confighelp",
							children: [
								"未检测到 ",
								e.name,
								"。",
								/* @__PURE__ */ J("a", {
									class: "externallink",
									href: e.download_url,
									target: "_blank",
									rel: "noreferrer",
									children: [
										"下载 ",
										e.name,
										/* @__PURE__ */ J("svg", {
											class: "externalmark",
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
										})
									]
								})
							]
						})) : null,
						e.windows === !1 ? /* @__PURE__ */ J("p", {
							class: "confighelp",
							children: "本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\\ 对应本机挂载文件夹。"
						}) : null
					]
				}),
				e.port_editable === !1 ? null : /* @__PURE__ */ J("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ J("label", {
							for: "configPort",
							children: "本机访问端口"
						}),
						/* @__PURE__ */ J("input", {
							id: "configPort",
							class: "geist-input",
							type: "text",
							inputMode: "numeric",
							value: f,
							"aria-invalid": b ? "true" : void 0,
							onInput: (e) => m(e.currentTarget.value)
						}),
						b ? /* @__PURE__ */ J("p", {
							class: "configbad",
							role: "alert",
							children: b
						}) : null,
						/* @__PURE__ */ J("p", {
							class: "confighelp",
							children: "浏览器地址里冒号后面的数字，一般不用改。"
						})
					]
				}),
				/* @__PURE__ */ J("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ J("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ J("input", {
							type: "checkbox",
							checked: h,
							onChange: (e) => g(e.currentTarget.checked)
						}), /* @__PURE__ */ J("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ J("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ J("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ J("span", { children: "保存后扫描并补全资料" })]
				}),
				S ? /* @__PURE__ */ J(At, { html: p(S, {
					variant: "error",
					label: "没有保存"
				}) }) : null
			]
		}), /* @__PURE__ */ J("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [/* @__PURE__ */ J("p", { children: e.port_editable === !1 ? "保存后 Peach 会重新载入配置。" : "保存后 Peach 会重新启动，端口改了就用新地址打开。" }), /* @__PURE__ */ J("button", {
				type: "submit",
				class: "geist-button primary",
				ref: j,
				children: "保存配置"
			})]
		})]
	});
}
function It({ receipt: e, data: t, error: n }) {
	return n || !t ? /* @__PURE__ */ J(At, {
		class: "configpage",
		html: p(n || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		})
	}) : /* @__PURE__ */ J("div", {
		class: "configpage",
		children: [
			t.startup ? /* @__PURE__ */ J("h2", {
				class: "configgroup",
				children: "通用"
			}) : null,
			t.startup ? /* @__PURE__ */ J(xt, {
				startup: t.startup,
				receipt: e
			}) : null,
			/* @__PURE__ */ J("h2", {
				class: "configgroup",
				children: "媒体"
			}),
			t.editable ? /* @__PURE__ */ J(Ft, {
				data: t,
				receipt: e
			}) : /* @__PURE__ */ J(At, { html: p(t.notice, {
				variant: "secondary",
				label: "只读"
			}) }),
			/* @__PURE__ */ J(Nt, { data: t }),
			t.peach_proxy || t.access ? /* @__PURE__ */ J("h2", {
				class: "configgroup",
				children: "网络与访问"
			}) : null,
			t.peach_proxy ? /* @__PURE__ */ J(vt, {
				initial: t.peach_proxy,
				receipt: e
			}) : null,
			t.access ? /* @__PURE__ */ J(ht, {
				initial: t.access,
				receipt: e
			}) : null,
			/* @__PURE__ */ J("h2", {
				class: "configgroup",
				children: "更新与维护"
			}),
			t.updates ? /* @__PURE__ */ J(_t, {
				initial: t.updates,
				initialJob: t.update_job
			}) : null,
			/* @__PURE__ */ J(Mt, { facts: t.facts }),
			t.uninstall ? /* @__PURE__ */ J(Ct, { uninstall: t.uninstall }) : null
		]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var Lt = Symbol.for("preact-signals");
function Rt() {
	if (X > 1) X--;
	else {
		var e, t = !1;
		for ((function() {
			var e = Kt;
			for (Kt = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); Ht !== void 0;) {
			var n = Ht;
			for (Ht = void 0, Ut++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && Xt(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (Ut = 0, X--, t) throw e;
	}
}
function zt(e) {
	if (X > 0) return e();
	Gt = ++Wt, X++;
	try {
		return e();
	} finally {
		Rt();
	}
}
var Bt, Y = void 0;
function Vt(e) {
	var t = Y, n = Bt;
	Y = void 0, Bt = void 0;
	try {
		return e();
	} finally {
		Y = t, Bt = n;
	}
}
var Ht = void 0, X = 0, Ut = 0, Wt = 0, Gt = 0, Kt = void 0, qt = 0;
function Jt(e) {
	if (Y !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== Y) return t = {
			i: 0,
			S: e,
			p: Y.s,
			n: void 0,
			t: Y,
			e: void 0,
			x: void 0,
			r: t
		}, Y.s !== void 0 && (Y.s.n = t), Y.s = t, e.n = t, 32 & Y.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = Y.s, t.n = void 0, Y.s.n = t, Y.s = t), t;
	}
}
function Z(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
Z.prototype.brand = Lt, Z.prototype.h = function() {
	return !0;
}, Z.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? Vt(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, Z.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && Vt(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, Z.prototype.subscribe = function(e) {
	var t = this;
	return an(function() {
		var n = t.value;
		Vt(function() {
			return e(n);
		});
	}, { name: "sub" });
}, Z.prototype.valueOf = function() {
	return this.value;
}, Z.prototype.toString = function() {
	return this.value + "";
}, Z.prototype.toJSON = function() {
	return this.value;
}, Z.prototype.peek = function() {
	var e = this;
	return Vt(function() {
		return e.value;
	});
}, Object.defineProperty(Z.prototype, "value", {
	get: function() {
		var e = Jt(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (Ut > 100) throw Error("Cycle detected");
			(function(e) {
				X !== 0 && Ut === 0 && e.l !== Gt && (e.l = Gt, Kt = {
					S: e,
					v: e.v,
					i: e.i,
					o: Kt
				});
			})(this), this.v = e, this.i++, qt++, X++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				Rt();
			}
		}
	}
});
function Yt(e, t) {
	return new Z(e, t);
}
function Xt(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function Zt(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function Qt(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function Q(e, t) {
	Z.call(this, void 0, t), this.x = e, this.s = void 0, this.g = qt - 1, this.f = 4;
}
Q.prototype = new Z(), Q.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === qt)) return !0;
	if (this.g = qt, this.f |= 1, this.i > 0 && !Xt(this)) return this.f &= -2, !0;
	var e = Y;
	try {
		Zt(this), Y = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return Y = e, Qt(this), this.f &= -2, !0;
}, Q.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	Z.prototype.S.call(this, e);
}, Q.prototype.U = function(e) {
	if (this.t !== void 0 && (Z.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, Q.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(Q.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = Jt(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function $t(e, t) {
	return new Q(e, t);
}
function en(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		X++;
		var n = Y;
		Y = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, tn(e), t;
		} finally {
			Y = n, Rt();
		}
	}
}
function tn(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, en(e);
}
function nn(e) {
	if (Y !== this) throw Error("Out-of-order effect");
	Qt(this), Y = e, this.f &= -2, 8 & this.f && tn(this), Rt();
}
function rn(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, Bt && Bt.push(this);
}
rn.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, rn.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, en(this), Zt(this), X++;
	var e = Y;
	return Y = this, nn.bind(this, e);
}, rn.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = Ht, Ht = this);
}, rn.prototype.d = function() {
	this.f |= 8, 1 & this.f || tn(this);
}, rn.prototype.dispose = function() {
	this.d();
};
function an(e, t) {
	var n = new rn(e, t);
	try {
		n.c();
	} catch (e) {
		throw n.d(), e;
	}
	var r = n.d.bind(n);
	return r[Symbol.dispose] = r, r;
}
//#endregion
//#region node_modules/@preact/signals/dist/signals.module.js
var on, sn, cn = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, ln = [];
an(function() {
	on = this.N;
})();
function un(e, t) {
	S[e] = t.bind(null, S[e] || function() {});
}
function dn(e) {
	if (sn) {
		var t = sn;
		sn = void 0, t();
	}
	sn = e && e.S();
}
function fn(e) {
	var t = this, n = e.data, r = mn(n);
	r.name = "ReactiveDom", r.value = n;
	var i = at(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = $t(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = $t(function() {
			return !Array.isArray(i.value) && !w(i.value);
		}), o = an(function() {
			if (this.N = _n, a.value) {
				var t = i.value;
				e.__v && e.__v.__e && e.__v.__e.nodeType === 3 && (e.__v.__e.data = t);
			}
		}), s = t.__$u.d;
		return t.__$u.d = function() {
			o(), s.call(this);
		}, [a, i];
	}, []), a = i[0], o = i[1];
	return a.value ? o.peek() : o.value;
}
fn.displayName = "ReactiveTextNode", Object.defineProperties(Z.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: fn
	},
	props: {
		configurable: !0,
		get: function() {
			var e = this;
			return { data: { get value() {
				return e.value;
			} } };
		}
	},
	__b: {
		configurable: !0,
		value: 1
	}
}), un("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof Z && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), un("__r", function(e, t) {
	if (e(t), t.type !== I) {
		dn();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return an(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				cn && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), dn(n);
	}
}), un("__e", function(e, t, n, r) {
	dn(), e(t, n, r);
}), un("diffed", function(e, t) {
	dn();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = pn(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function pn(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = Yt(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: an(function() {
			this.N = _n;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
un("unmount", function(e, t) {
	if (typeof t.type == "string") {
		var n = t.__e;
		if (n) {
			var r = n.U;
			if (r) for (var i in n.U = void 0, r) {
				var a = r[i];
				a && a.d();
			}
		}
		var o = t.__np;
		if (o) {
			var s = t.props;
			for (var c in o) s[c] = o[c];
		}
		t.__np = void 0;
	} else {
		var l = t.__c;
		if (l) {
			var u = l.__$u;
			u && (l.__$u = void 0, u.d());
		}
	}
	e(t);
}), un("__h", function(e, t, n, r) {
	r < 3 && (t.__$f |= 2), e(t, n, r);
}), ce.prototype.shouldComponentUpdate = function(e, t) {
	if (this.__R) return !0;
	var n = this.__$u, r = n && n.s !== void 0;
	for (var i in t) return !0;
	if (this.__f || typeof this.u == "boolean" && !0 === this.u) {
		var a = 2 & this.__$f;
		if (!(r || a || 4 & this.__$f) || 1 & this.__$f) return !0;
	} else if (!(r || 4 & this.__$f) || 3 & this.__$f) return !0;
	for (var o in e) if (o !== "__source" && e[o] !== this.props[o]) return !0;
	for (var s in this.props) if (!(s in e)) return !0;
	return !1;
};
function mn(e, t) {
	return at(function() {
		return Yt(e, t);
	}, []);
}
var hn = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function gn() {
	zt(function() {
		for (var e; e = ln.shift();) on.call(e);
	});
}
function _n() {
	ln.push(this) === 1 && (S.requestAnimationFrame || hn)(gn);
}
//#endregion
//#region src/state/quality-goals.ts
var vn = "/api/quality-goals?limit=200", yn = {
	data: null,
	error: ""
}, bn = Yt(yn), xn = 0, Sn = $t(() => bn.value);
$t(() => bn.value.data?.total ?? null);
function Cn() {
	xn += 1, bn.value = yn;
}
async function wn(e) {
	let t = xn += 1;
	try {
		let n = await B(vn, e);
		return t === xn && (bn.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === xn && (bn.value = {
			data: null,
			error: z(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var Tn = (e, t) => wn(t), En = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function Dn({ openItem: t, javTitleHtml: n, javDisplayName: a, srcBadge: o }) {
	let { data: s, error: c } = Sn.value;
	if (c) return /* @__PURE__ */ J("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: p(c, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let l = s?.items ?? [];
	return l.length ? /* @__PURE__ */ J("div", {
		class: "qualitylist",
		children: l.map((s) => /* @__PURE__ */ J("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ J("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${a(s)}`,
				onClick: () => t(s.id),
				children: /* @__PURE__ */ J("img", {
					src: En(s),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ J("div", { children: [
				/* @__PURE__ */ J("h3", { children: /* @__PURE__ */ J("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => t(s.id),
					dangerouslySetInnerHTML: { __html: n(s) }
				}) }),
				/* @__PURE__ */ J("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ J("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: o(s.location, s.cost) }
						}),
						/* @__PURE__ */ J("span", { children: e[s.location] ?? s.location }),
						/* @__PURE__ */ J("span", { children: r(s.duration) }),
						/* @__PURE__ */ J("span", { children: i(s.size ?? 0) })
					]
				}),
				s.reason ? /* @__PURE__ */ J("p", { children: s.reason }) : null
			] })]
		}, s.id))
	}) : /* @__PURE__ */ J("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: u("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/jobs.ts
async function On(e) {
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
function kn(e) {
	let t = document.createElement("div");
	e.host.hidden = !0, t.dataset.followJob = "", t.setAttribute("aria-live", "polite"), e.host.prepend(t);
	let n = e.storageKey || "peach-follow-job", r = sessionStorage.getItem(n) || void 0, i = !1;
	On({
		read: e.read,
		active: () => !i && e.active() && t.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (a) => {
			let o = a.status === "running";
			if (e.host.hidden = !o, e.busy(o), o) {
				r = a.job_id, r && sessionStorage.setItem(n, r);
				let i = a.current, o = (i?.attempt || 1) > 1 ? ` · 第 ${i?.attempt}/${i?.max_attempts} 次尝试${i?.retry_in ? `，${i.retry_in} 秒后重试` : ""}` : "", s = (a.message || (e.title ? e.title + (a.total ? `：已完成 ${a.checked || 0}/${a.total}` : "") : "") || (a.total ? `${a.older ? "抓取历史" : "检查更新"}：已完成 ${a.checked || 0}/${a.total} 个来源` : "正在准备检查任务…")) + (i ? ` · ${i.label || i.provider || ""}${o}` : ""), c = e.loading(s) + ((a.total || 0) > 0 ? e.progress(a.checked || 0, a.total) : "");
				t.innerHTML = e.container ? e.container(c) : c;
			} else if (r && r === a.job_id) r = void 0, i = !0, e.host.hidden = a.status !== "failed", sessionStorage.removeItem(n), t.innerHTML = a.status === "failed" ? e.note(a.error || "检查失败") : "", e.complete(a);
			else {
				if (r && a.status === "idle") {
					e.host.hidden = !1, t.innerHTML = e.note("任务状态已失效，请重新发起任务"), sessionStorage.removeItem(n), i = !0;
					return;
				}
				t.innerHTML = "";
			}
		},
		disconnected: () => {
			e.host.hidden = !1, t.innerHTML = e.note("暂时无法读取进度，正在重新连接…");
		}
	});
}
//#endregion
//#region src/islands/scraping.tsx
var An = (e, t) => B("/api/scraping", t);
function jn({ value: e, onChange: t }) {
	let n = q(null), r = q(t);
	return r.current = t, K(() => {
		let t = n.current;
		t.innerHTML = g([["peach", "Peach 代理"], ["direct", "直接连接"]], e, { label: "连接方式" });
		let i = b(t.firstElementChild), a = () => r.current(i.value);
		return i.addEventListener("change", a), () => {
			i.disabled = !0, i.removeEventListener("change", a), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ J("div", {
		ref: n,
		class: "scraping-network"
	});
}
function Mn({ source: e, toast: t }) {
	let [r, i] = W(e), [a, o] = W(e.network), [s, c] = W(""), [l, u] = W(""), [f, m] = W("paste"), [h, g] = W(""), [_, y] = W(!1), [b, x] = W(""), [S, C] = W([]), w = q(null), T = q(null);
	K(() => {
		T.current?.querySelectorAll("footer button").forEach((e) => v(e, _));
	}, [_]);
	let E = q(new AbortController());
	G(() => () => E.current.abort(), []);
	async function D(n) {
		if (!_) {
			y(!0), x(""), C([]);
			try {
				if (n === "check") {
					let t = await V("/api/scraping/check", { source: e.source }, "POST", E.current.signal);
					E.current.signal.aborted || C(t.results);
				} else {
					let r = await V("/api/scraping/settings", {
						source: e.source,
						network: a,
						cookie: s,
						cookies_text: l,
						revoke: n === "revoke"
					}, "POST", E.current.signal);
					E.current.signal.aborted || (i(r.saved), c(""), u(""), g(""), w.current && (w.current.value = ""), t(n === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				E.current.signal.aborted || x(z(e));
			} finally {
				E.current.signal.aborted || y(!1);
			}
		}
	}
	return /* @__PURE__ */ J("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ J("form", {
			ref: T,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), D("save");
			},
			children: [/* @__PURE__ */ J("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ J("div", {
						class: "geist-fieldset-heading",
						children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: d(`scraping-${e.source}`, e.label) } }), /* @__PURE__ */ J("a", {
							class: "scraping-url externallink",
							href: e.login,
							target: "_blank",
							rel: "noopener noreferrer",
							children: [
								/* @__PURE__ */ J("img", {
									src: n(e.login),
									alt: "",
									width: "16",
									height: "16",
									loading: "lazy",
									onError: (e) => e.currentTarget.remove()
								}),
								/* @__PURE__ */ J("span", { children: e.login }),
								/* @__PURE__ */ J("svg", {
									class: "externalmark",
									viewBox: "0 0 24 24",
									"aria-hidden": "true",
									children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
								})
							]
						})]
					}),
					/* @__PURE__ */ J("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ J(jn, {
							value: a,
							onChange: o
						})]
					}),
					a === "peach" && /* @__PURE__ */ J("a", {
						class: "geist-text-link",
						href: "/configuration#peachProxy",
						children: "配置 Peach 代理"
					}),
					e.accepts_cookie && /* @__PURE__ */ J(I, { children: [
						/* @__PURE__ */ J("p", { children: r.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ J("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ J("label", { children: [/* @__PURE__ */ J("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: f === t,
								onChange: () => {
									m(t), c(""), u(""), g("");
								}
							}), /* @__PURE__ */ J("span", { children: n })] }, t))
						}),
						f === "paste" ? /* @__PURE__ */ J("label", { children: ["Cookie", /* @__PURE__ */ J("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: s,
							disabled: _,
							onInput: (e) => c(e.currentTarget.value)
						})] }) : /* @__PURE__ */ J("label", {
							class: "scraping-file",
							children: ["Netscape Cookie 文件（.txt）", /* @__PURE__ */ J("span", {
								class: "scraping-file-control",
								children: [
									/* @__PURE__ */ J("span", {
										class: "geist-button",
										children: "选择文件"
									}),
									/* @__PURE__ */ J("span", {
										class: "scraping-file-name",
										children: h || "未选择文件"
									}),
									/* @__PURE__ */ J("input", {
										ref: w,
										type: "file",
										accept: ".txt",
										disabled: _,
										onChange: async (e) => {
											let t = e.currentTarget.files?.[0];
											if (!t) {
												u(""), g("");
												return;
											}
											if (u(""), t.size > 262144) {
												x("Cookie 文本超过 256 KiB"), e.currentTarget.value = "";
												return;
											}
											y(!0);
											try {
												let e = await t.text();
												E.current.signal.aborted || (u(e), g(t.name));
											} catch {
												E.current.signal.aborted || x("Cookie 文件未读取，请重新选择");
											} finally {
												E.current.signal.aborted || y(!1);
											}
										}
									})
								]
							})]
						})
					] }),
					b && /* @__PURE__ */ J("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: p(b, { variant: "error" }) }
					}),
					S.map((t) => /* @__PURE__ */ J("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: p(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ J("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					e.accepts_cookie && r.cookie_saved && /* @__PURE__ */ J("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void D("revoke"),
						children: "撤销 Cookie"
					}),
					/* @__PURE__ */ J("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void D("check"),
						children: "检查连接"
					}),
					/* @__PURE__ */ J("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					})
				]
			})]
		})
	});
}
function Nn({ data: e, error: t, toast: n }) {
	let [r, i] = W(""), [a, o] = W(!1), [s, c] = W(""), l = q(null);
	K(() => v(l.current, a), [a]);
	let u = q(new AbortController()), f = q(0);
	async function m(e = !1) {
		let t = ++f.current;
		await On({
			read: (e) => B("/api/scraping/cover", e),
			active: () => !u.current.signal.aborted && t === f.current,
			render: (t) => {
				o(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && c(t.error || "采集未取得"), t.status === "complete" && !e && n(t.result || "封面采集完成");
			},
			disconnected: () => c("连接中断，正在重新读取后台进度")
		});
	}
	G(() => (m(!0), () => u.current.abort()), []);
	async function h() {
		if (!a) {
			f.current++, o(!0), c("");
			try {
				await V("/api/scraping/cover", { code: r }, "POST", u.current.signal), await m();
			} catch (e) {
				u.current.signal.aborted || (o(!1), c(z(e)));
			}
		}
	}
	return t ? /* @__PURE__ */ J("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: p(t, { variant: "error" }) }
	}) : /* @__PURE__ */ J("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ J("p", { children: "高清图片可能需要代理才能下载，请先检查连接。" }),
			/* @__PURE__ */ J("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ J("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: d("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ J("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), h();
							},
							children: [/* @__PURE__ */ J("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: r,
								disabled: a,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => i(e.currentTarget.value)
							}), /* @__PURE__ */ J("button", {
								ref: l,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						s && /* @__PURE__ */ J("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: p(s, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ J(Mn, {
				source: e,
				toast: n
			}, e.source))
		]
	});
}
//#endregion
//#region src/islands/library-processing.tsx
var Pn = (e, t) => B("/api/library-processing", t);
function Fn({ data: e, error: t, toast: n, onComplete: r, mode: i, monitor: a }) {
	let [o, s] = W(e || { status: "idle" }), [c, l] = W(t), [u, m] = W(!1), [g, _] = W(!1), y = q(new AbortController()), b = q(0), x = q(o.status), S = q(null), C = u || o.status === "running";
	K(() => v(S.current, C), [C]);
	async function w() {
		let e = ++b.current;
		await On({
			read: (e) => B("/api/library-processing", e),
			active: () => !y.current.signal.aborted && b.current === e,
			keepWatching: i === "notice" || !!a,
			render: (e) => {
				s(e), l(""), e.status === "complete" && x.current === "running" && i !== "notice" && (_(!0), n("已完成扫描与资料采集")), x.current === "running" && (e.status === "complete" || e.status === "failed") && r?.(), x.current = e.status;
			},
			disconnected: () => l("连接中断，正在重新读取处理进度")
		});
	}
	G(() => ((o.status === "running" || i === "notice" || a) && w(), () => y.current.abort()), []);
	async function T() {
		if (!C) {
			m(!0), l(""), _(!1);
			try {
				let e = await V("/api/library-processing", {}, "POST", y.current.signal);
				if (y.current.signal.aborted) return;
				x.current = e.status, s(e), m(!1), await w();
			} catch (e) {
				y.current.signal.aborted || (l(z(e)), m(!1));
			}
		}
	}
	if (i === "notice") {
		if (!c && o.status !== "running" && o.status !== "failed") return null;
		let e = c || (o.status === "failed" ? "扫描与资料采集未完成" : `${o.stage || "正在整理馆藏"}${o.total ? ` · ${o.checked || 0} / ${o.total}` : ""}`);
		return /* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: h(e, {
			variant: o.status === "failed" ? "error" : c ? "warning" : "gray",
			href: "/data-cleanup#libraryProcessing",
			label: c || o.status === "failed" ? "查看并处理" : "查看进度",
			value: o.checked || 0,
			...o.status === "running" && o.total !== void 0 ? { max: o.total } : {}
		}) } });
	}
	return /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J("div", {
		class: "geist-fieldset-content library-processing",
		children: [
			/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: d("cleanupScrapingTitle", "扫描与采集") } }),
			/* @__PURE__ */ J("p", { children: "扫描媒体文件夹，导入已有资料，采集缺失信息。" }),
			/* @__PURE__ */ J("div", {
				"aria-live": "polite",
				children: [
					o.status === "running" && /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: f(`${o.stage || "正在处理"}${o.total ? ` · ${o.checked || 0} / ${o.total}` : ""}`) } }), !!o.total && /* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: Fe(`已处理 ${o.checked || 0} / ${o.total} 个视频`, o.checked || 0, o.total) } })] }),
					(c || o.status === "failed") && /* @__PURE__ */ J("div", {
						role: "alert",
						onClick: (e) => {
							e.target.closest("[data-note-action]") && T();
						},
						dangerouslySetInnerHTML: { __html: p(c || o.error || "处理未完成，请重试", {
							variant: "error",
							filled: !0,
							actionLabel: o.status === "failed" ? "重试未完成项" : ""
						}) }
					}),
					o.status === "failed" && !!o.issues?.length && /* @__PURE__ */ J("ul", { children: o.issues.slice(0, 20).map((e) => /* @__PURE__ */ J("li", { children: [
						e.asset_id ? /* @__PURE__ */ J("a", {
							href: `/item/${e.asset_id}`,
							children: "查看视频"
						}) : null,
						e.asset_id ? "：" : "",
						e.message
					] })) }),
					g && /* @__PURE__ */ J("div", {
						class: "library-processing-result",
						dangerouslySetInnerHTML: { __html: p(`已扫描 ${o.scanned || 0} 个文件，识别 ${o.identified || 0} 个番号，整理 ${o.candidates || 0} 组资料候选。`, {
							variant: "success",
							label: "处理完成"
						}) }
					})
				]
			})
		]
	}), /* @__PURE__ */ J("footer", {
		class: "geist-fieldset-footer",
		"data-geist-fieldset-footer": !0,
		children: [
			/* @__PURE__ */ J("a", {
				class: "geist-button",
				href: "/scraping",
				children: "采集来源"
			}),
			!!o.candidates && /* @__PURE__ */ J("a", {
				class: "geist-button",
				href: "/review",
				children: "复核资料"
			}),
			o.status !== "failed" && /* @__PURE__ */ J("button", {
				ref: S,
				type: "button",
				class: "geist-button primary",
				onClick: () => void T(),
				children: "扫描并补全资料"
			})
		]
	})] });
}
//#endregion
//#region src/state/index.ts
var In = { "quality-goals": {
	refresh: wn,
	reset: Cn
} }, Ln = () => Object.keys(In);
async function Rn(e) {
	let t = In[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/review-evidence.ts
var zn = (e = "") => /^https?:\/\//i.test(e) ? e : "";
function Bn(e = "") {
	let n = zn(e) || (e.startsWith("/") && !e.startsWith("//") ? e : "");
	return `<div class="reviewimage" data-review-picture><span class="reviewimageempty"${n ? " hidden" : ""}>未取得来源图片</span>${n ? `<img src="${t(n)}" alt="来源候选图片" loading="lazy">` : ""}</div>`;
}
function Vn(e) {
	let n = zn(e.profile_url), r = (e.preview_assets || []).slice(0, 6), i = Math.max(0, Number(e.video_count || e.videos || 0));
	return `<section class="reviewidentityevidence"><h5>候选身份：${t(e.babepedia_name || "未标注")}</h5>
    <div class="reviewevidenceactions">${n ? `<a class="geist-button externallink" href="${t(n)}" target="_blank" rel="noopener noreferrer">来源资料<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a>` : ""}
    <button type="button" class="geist-button" data-entity-kind="creator" data-entity-name="${t(e.creator || "")}">查看全部 ${i.toLocaleString()} 部作品</button></div>
    ${Bn(e.preview_url)}
    <p>通过后记录身份判断。</p>
    ${r.length ? `<h5>本地作品样本</h5><div class="reviewevidencesamples">${r.map((e) => `<div class="reviewevidencesample">
      <button class="geist-button" type="button" data-review-open-item="${e.id}"><span data-middle-truncate title="${t(e.name)}">${t(e.name)}</span></button>
      <button class="geist-button" type="button" data-review-reveal="${e.id}" aria-label="打开 ${t(e.name)} 的文件位置">文件位置</button>
    </div>`).join("")}</div>` : "<p>暂无本地作品样本，打开全部作品核对。</p>"}</section>`;
}
function Hn(e) {
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
//#region src/review-bulk.ts
var Un = () => ({
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
function Wn(e) {
	let t = e?.querySelector(".reviewcontrols");
	if (!e || !t || t.offsetParent === null) return;
	let n = e.closest("main");
	n && e.style.setProperty("--review-edge", getComputedStyle(n).paddingLeft), e.style.setProperty("--review-controls-height", `${t.getBoundingClientRect().height}px`);
	for (let n of [t, ...e.querySelectorAll(".reviewgroupbar")]) {
		let e = parseFloat(getComputedStyle(n).top);
		n.classList.toggle("is-stuck", n.offsetParent !== null && window.scrollY > 0 && Number.isFinite(e) && Math.abs(n.getBoundingClientRect().top - e) <= 1);
	}
}
function Gn(e, t) {
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
function Kn(e, t) {
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
function qn(e, t, n, r, i) {
	let a = e.anchor === null ? -1 : t.indexOf(e.anchor), o = t.indexOf(n);
	r && a >= 0 && o >= 0 ? t.slice(Math.min(a, o), Math.max(a, o) + 1).forEach((t) => e.selected.add(t)) : i ? e.selected.add(n) : e.selected.delete(n), e.anchor = n;
}
async function Jn(e, t, n, r) {
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
				message: z(e)
			});
		}
	}
	return {
		completed: a,
		failures: i
	};
}
function Yn(e) {
	return e.length ? [...new Set(e.flatMap((e) => e.candidates?.map((e) => e.source || "") || []))].filter((t) => t && e.every((e) => e.candidates?.filter((e) => e.source === t).length === 1)) : [];
}
function Xn(e, t) {
	let n = e.querySelector(".reviewlist");
	if (!n || !t.rows.length || t.locked) return;
	let r = t.state, i = [...n.querySelectorAll("[data-review-key]")];
	t.category !== void 0 && r.category !== t.category && (r.category = t.category, r.filter = "", r.groupBy = "candidates", r.anchor = null);
	let a = Gn(t.rows, t.metadata);
	a.some((e) => e[0] === r.groupBy) || (r.groupBy = "candidates", r.filter = "");
	let o = Kn(t.rows, r.groupBy);
	o.some((e) => e.key === r.filter) || (r.filter = "");
	let s = () => [...n.querySelectorAll("[data-review-key]")].filter((e) => !e.closest("[hidden]")), l = () => s().filter((e) => r.selected.has(e.dataset.reviewKey)), u = () => t.rows.filter((e) => l().some((t) => t.dataset.reviewKey === e.item_key)), d = (e) => !e.querySelector("[data-review-status=\"approved\"]")?.disabled, f = (e, t = "") => {
		let n = document.createElement("button");
		return n.type = "button", n.className = `geist-button ${t}`.trim(), n.textContent = e, n;
	}, p = document.createElement("div");
	p.className = "reviewbulkbar reviewbulktoolbar", p.setAttribute("role", "group"), p.setAttribute("aria-label", "复核批量操作");
	let m = document.createElement("div");
	m.className = "reviewgroupby", m.innerHTML = g(a, r.groupBy, { label: "筛选分组方式" });
	let h = b(m.firstElementChild);
	m.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), h.addEventListener("change", () => {
		if (r.busy || !a.some((e) => e[0] === h.value)) return;
		r.groupBy = h.value, r.filter = "", r.anchor = null;
		let n = e.parentElement;
		t.refresh(), n?.querySelector(".reviewgroupby button")?.focus({ preventScroll: !0 });
	});
	let _ = document.createElement("div");
	_.className = "reviewcategoryfilter", _.hidden = o.length < 2, _.innerHTML = g([[
		"",
		"全部分类",
		"list-filter"
	], ...o.map((e) => [
		e.key,
		`${e.title} · ${e.rows.length}`,
		"list-filter"
	])], r.filter, { label: r.groupBy === "field" ? "筛选字段分类" : "筛选当前分类" });
	let y = _.querySelector("[data-select-menu]");
	if (y) {
		let e = document.createElement("div");
		e.setAttribute("role", "group"), e.setAttribute("aria-label", r.groupBy === "field" ? "字段分类" : "当前分类");
		let t = document.createElement("div");
		t.className = "reviewfilterheading", t.textContent = e.getAttribute("aria-label"), t.setAttribute("aria-hidden", "true"), e.append(t, ...Array.from(y.children).slice(1)), y.append(e);
	}
	let x = b(_.firstElementChild);
	_.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), x.addEventListener("change", () => {
		if (r.busy || x.value && !o.some((e) => e.key === x.value)) return;
		r.filter = x.value, r.anchor = null;
		let n = e.parentElement;
		t.refresh(), n?.querySelector(".reviewcategoryfilter button")?.focus({ preventScroll: !0 });
	});
	let S = f("全选本页"), C = f("通过所选", "primary"), w = f("拒绝所选", "error"), T = document.createElement("span");
	T.className = "reviewselectedcount selectiondockcount", T.setAttribute("role", "status");
	let E = document.createElement("div");
	E.className = "reviewbulksource", E.hidden = !t.metadata;
	let D = document.createElement("p");
	D.className = "reviewstate reviewbulkfeedback", D.setAttribute("role", "status");
	let O = document.createElement("div");
	O.className = "reviewbulkdecisions", O.append(C, w);
	let k = document.createElement("div");
	k.className = "selectiondock reviewdock", k.setAttribute("role", "group"), k.setAttribute("aria-label", "复核所选项目");
	let A = f("取消选择");
	k.append(T, E, O, A, D), p.append(m, _, S);
	let j = e.querySelector(".reviewcontrols");
	j ? j.append(p) : n.before(p), e.append(k), n.classList.add("reviewgroups");
	let ee = () => {
		r.selected.clear(), r.anchor = null, N();
	};
	A.onclick = () => {
		r.busy || (ee(), S.focus({ preventScroll: !0 }));
	}, S.onclick = () => {
		if (r.busy) return;
		let e = s(), t = l().length === e.length;
		e.forEach((e) => t ? r.selected.delete(e.dataset.reviewKey) : r.selected.add(e.dataset.reviewKey)), N();
	}, C.onclick = () => P("approved", C), w.onclick = () => P("rejected", w);
	let M = [];
	for (let e of o) {
		let t = e.rows.map((e) => i.find((t) => t.dataset.reviewKey === e.item_key)).filter((e) => !!e), a = document.createElement("section");
		a.className = "reviewgroup", a.hidden = !!r.filter && e.key !== r.filter;
		let o = document.createElement("div");
		o.className = "reviewbulkbar reviewgroupbar";
		let l = document.createElement("h3");
		l.textContent = `${e.title} · ${t.length}`;
		let u = f("全选本组"), d = document.createElement("div");
		d.className = "reviewlist", o.append(l, u), a.append(o, d), n.append(a), u.onclick = () => {
			if (r.busy) return;
			let e = t.every((e) => r.selected.has(e.dataset.reviewKey));
			t.forEach((t) => e ? r.selected.delete(t.dataset.reviewKey) : r.selected.add(t.dataset.reviewKey)), N();
		}, M.push(() => {
			u.textContent = t.every((e) => r.selected.has(e.dataset.reviewKey)) ? "清空本组" : "全选本组";
		});
		for (let e of t) {
			d.append(e);
			let t = e.dataset.reviewKey;
			r.errors.has(t) && (e.querySelector(".reviewstate").textContent = r.errors.get(t));
			let n = e.querySelector("h4,.reviewentity b") || e, i = document.createElement("label");
			i.className = "reviewpickitem", i.innerHTML = c();
			let a = i.querySelector("input");
			if (a.setAttribute("aria-label", `选择 ${e.querySelector("legend")?.textContent || n.textContent || t}`), n !== e) {
				let e = document.createElement("span");
				e.className = "reviewpickname", e.append(...n.childNodes), n.classList.add("reviewpickheading"), n.append(i, e);
			} else e.prepend(i);
			let o = (e, n) => {
				qn(r, s().map((e) => e.dataset.reviewKey), t, e, n), N();
			};
			if (i.addEventListener("mousedown", (e) => {
				e.shiftKey && e.preventDefault();
			}), i.addEventListener("click", (e) => {
				e.target !== a && (e.preventDefault(), r.busy || (a.focus(), o(e.shiftKey, !a.checked)));
			}), a.addEventListener("click", (e) => {
				r.busy || o(e.shiftKey, a.checked);
			}), a.addEventListener("keydown", (n) => {
				if (!(r.busy || !n.shiftKey)) {
					if (n.key === " ") n.preventDefault(), o(!0, !0);
					else if (n.key === "ArrowDown" || n.key === "ArrowUp") {
						n.preventDefault();
						let i = s(), a = i[i.indexOf(e) + (n.key === "ArrowDown" ? 1 : -1)];
						a && (r.anchor === null && (r.anchor = t), qn(r, i.map((e) => e.dataset.reviewKey), a.dataset.reviewKey, !0, !0), N(), a.querySelector(".reviewpickitem input")?.focus());
					}
				}
			}), M.push(() => {
				a.checked = r.selected.has(t);
			}), r.assets.has(t)) {
				let n = r.assets.get(t), i = [...e.querySelectorAll("[data-review-asset]")];
				i.forEach((e) => {
					let t = n.includes(Number(e.dataset.reviewAsset));
					e.setAttribute("aria-pressed", String(t)), e.classList.toggle("picked", t);
				});
				let a = e.querySelector("[data-picked-count]");
				a && (a.textContent = `已选 ${n.length} / ${i.length}`);
			}
			e.addEventListener("click", (n) => {
				n.target.closest("[data-review-asset],[data-pick-all],[data-pick-none]") && r.assets.set(t, [...e.querySelectorAll("[data-review-asset][aria-pressed=\"true\"]")].map((e) => Number(e.dataset.reviewAsset)));
			});
			for (let n of e.querySelectorAll("input[type=\"radio\"]")) r.choices.has(t) && (n.checked = r.choices.get(t) === n.value), n.addEventListener("change", () => {
				n.checked && r.choices.set(t, n.value), N();
			});
		}
	}
	e.addEventListener("keydown", (t) => {
		r.busy || !e.contains(n) || (t.key === "Escape" && r.selected.size && (t.preventDefault(), t.stopPropagation(), ee()), (t.ctrlKey || t.metaKey) && t.key.toLowerCase() === "a" && !t.target.matches("textarea,input:not([type=\"checkbox\"]):not([type=\"radio\"])") && (t.preventDefault(), t.stopPropagation(), s().forEach((e) => r.selected.add(e.dataset.reviewKey)), N()));
	});
	let te = "";
	function N() {
		let e = l();
		S.textContent = e.length === s().length ? "清空当前选择" : r.filter ? "全选当前分类" : "全选本页", k.hidden = !e.length, T.textContent = `已选 ${e.length} 项`, C.disabled = !e.length || e.some((e) => !d(e)), w.disabled = !e.length;
		let n = Yn(u());
		E.hidden = !t.metadata || !u().some((e) => (e.candidates?.length || 0) > 1);
		let i = e.length && !n.length ? "所选项目无共同来源" : "统一选择来源", a = JSON.stringify([i, n]);
		if (a !== te) {
			te = a, E.innerHTML = g([["", i], ...n.map((e) => [e, e])], "", { label: "统一选择来源" });
			let e = b(E.firstElementChild);
			e.disabled = !n.length, e.addEventListener("change", () => {
				if (!(r.busy || !Yn(u()).includes(e.value))) {
					for (let n of l()) {
						let i = t.rows.find((e) => e.item_key === n.dataset.reviewKey).candidates.find((t) => t.source === e.value);
						n.querySelectorAll("input[type=\"radio\"]").forEach((e) => {
							e.checked = e.value === i.candidate_key;
						}), r.choices.set(n.dataset.reviewKey, i.candidate_key);
					}
					D.textContent = `已选择 ${e.value}，点击通过所选采用。`;
				}
			});
		}
		M.forEach((e) => e());
	}
	async function P(n, i) {
		if (r.busy || !l().length) return;
		let a = l().map((e) => ({
			key: e.dataset.reviewKey,
			payload: {
				...t.payload(e),
				status: n
			}
		}));
		if (n === "approved" && t.metadata && a.some((e) => !e.payload.candidate_key)) {
			D.textContent = "请先为所选的多来源候选选择来源。", l().find((e) => !e.querySelector("input[type=\"radio\"]:checked"))?.querySelector("input[type=\"radio\"]")?.focus();
			return;
		}
		r.busy = !0, D.textContent = `正在处理 0 / ${a.length}`, v(i, !0);
		let o = [...e.querySelectorAll("button,input")], s = o.map((e) => e.getAttribute("aria-disabled"));
		o.forEach((e) => e.setAttribute("aria-disabled", "true"));
		let c = (e) => {
			e instanceof KeyboardEvent && e.key === "Tab" || (e.preventDefault(), e.stopImmediatePropagation());
		};
		e.addEventListener("click", c, !0), e.addEventListener("keydown", c, !0);
		let u = 0, d = await Jn(a, async (e) => {
			try {
				return await t.submit(e);
			} finally {
				u++, t.active() && (D.textContent = `正在处理 ${u} / ${a.length}`);
			}
		}, (e) => {
			r.selected.delete(e), r.errors.delete(e), t.applied(e);
		}, t.active);
		if (r.busy = !1, e.removeEventListener("click", c, !0), e.removeEventListener("keydown", c, !0), o.forEach((e, t) => {
			let n = s[t];
			n === null ? e.removeAttribute("aria-disabled") : e.setAttribute("aria-disabled", n);
		}), v(i, !1), !t.active()) return;
		t.notify(`已${n === "approved" ? "通过" : "拒绝"} ${d.completed} 项${d.failures.length ? `，${d.failures.length} 项未完成` : ""}`), d.failures.forEach((e) => r.errors.set(e.key, e.message));
		let f = e.parentElement;
		t.refresh(), f?.querySelector(".reviewbulktoolbar button")?.focus({ preventScroll: !0 });
	}
	N(), Wn(e);
}
//#endregion
//#region src/native-image.ts
function Zn(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function Qn(e, t, n, r, i = 1) {
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
function $n(e, t) {
	return `<section data-skeleton="entity/${e}" role="status" aria-label="正在读取资料">
    <span class="sr-only">正在读取资料</span><div aria-hidden="true">
    <div class="entityhero"><div class="entityportrait ${e === "studio" || e === "agency" ? "square " : ""}skeleton"></div>
      <div class="entityskeletontext"><div class="entitytitle"><h2 class="skeleton">&nbsp;</h2></div>
      <div class="alias"><span class="skeleton"></span></div>
      <div class="entitylinks"><span class="skeleton"></span></div></div></div>
    <section class="entitytagbar"><div class="entitytags"><span class="skeleton entitymediaskeleton"></span><span class="skeleton entitymediaskeleton"></span></div></section>
    <div class="entitysection">${t}</div></div></section>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var er = [
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
	"state",
	"jav",
	"thumb"
];
function tr() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function nr(e, t) {
	let n = new URLSearchParams();
	for (let t of er) e[t] && n.set(t, e[t]);
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
function rr({ kind: e = "catalog", filtered: t = !1, jav: n = !1, configurable: r = !1, online: i = !1 } = {}) {
	let a = r ? "<a class=\"geist-button primary\" href=\"/configuration\">添加内容</a>" : "", o = "<a class=\"geist-button\" href=\"/follow-manage\">添加来源</a>";
	return t || n ? u("search", n ? "还没有符合条件的 JAV 作品" : "没有符合条件的内容", n ? "已扫描但尚未补充发行资料的视频可在全部内容中查看。" : "清除筛选或搜索条件后查看全部内容。", { actions: "<a class=\"geist-button primary\" href=\"/?loc=&thumb=0\">查看全部内容</a>" }) : e === "catalog" ? u("play", "还没有视频", "添加媒体文件夹或关注来源，开始建立你的馆藏。", { actions: a + o }) : u(e === "tags" ? "tags" : "user-round", "还没有" + ({
		tags: "标签",
		performers: "艺人",
		creators: "创作者",
		studios: "厂牌",
		agencies: "事务所",
		series: "系列"
	}[e] || "资料"), i ? "添加关注来源并获取内容后，这里会显示对应标签。" : "添加内容并补充资料后，这里会显示对应信息。", { actions: i ? o : a + o });
}
//#endregion
//#region src/sidebar.ts
function ir(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function ar(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function or(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function sr(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function cr(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function lr() {
	return `<div class="cleanuppage" data-skeleton="cleanup" aria-busy="true" aria-label="正在读取数据管理状态">
    <div class="cleanupgrid">${[
		[
			"扫描与采集",
			"扫描并补全资料",
			"扫描媒体文件夹，导入已有资料，采集缺失信息。"
		],
		[
			"垃圾文件",
			"查看垃圾文件",
			""
		],
		[
			"重复文件",
			"查看重复文件",
			""
		],
		[
			"空文件夹",
			"删除空文件夹",
			""
		],
		[
			"人工复核",
			"查看候选",
			""
		],
		[
			"回收站",
			"查看回收站",
			""
		],
		[
			"高清版",
			"查看高清版",
			""
		]
	].map(([e, t, n], r) => `
      <section class="cleanupfieldset" data-geist-fieldset aria-labelledby="cleanup-loading-${r}">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-${r}">${e}</h3>
          ${n ? `<p>${n}</p>` : "<strong><span class=\"skeleton cleanup-count-skeleton\" aria-hidden=\"true\"></span></strong>"}
          ${r === 3 ? "<p class=\"cleanupmeta\"><span class=\"skeleton cleanup-count-skeleton\" aria-hidden=\"true\"></span></p>" : ""}</div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button"${r === 3 ? " class=\"danger\"" : ""} disabled>${r === 3 ? "<svg aria-hidden=\"true\"><use href=\"#i-trash\"></use></svg><span>" + t + "</span>" : t}</button></footer>
      </section>`).join("")}</div></div>`;
}
function ur(e, t = !1, n = !1) {
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
var dr = "peach-taste-guide-dismissed";
function fr(e, t) {
	y(e, ".taste-history-guide", "taste-guide-collapse");
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(dr, "1"), n.remove();
	});
}
//#endregion
//#region src/resource-sync.ts
var $ = (e = 0) => Number(e).toLocaleString(), pr = {
	local: "本地磁盘",
	115: "115",
	pikpak: "PikPak"
};
function mr(e, t) {
	let n = e.cache || {
		files: 0,
		bytes: 0
	}, r = !!(e.missing || n.files);
	return `<div class="resourcepanel" data-geist-fieldset><div class="resourcesources">${(e.sources || []).map((e) => `<article>
    <div class="resourcesourcetitle"><b>${pr[e.location] || "媒体来源"}</b><span class="${e.online ? "online" : "offline"}">${e.online ? "可访问" : "离线，已跳过"}</span></div>
    <strong>${e.online ? `${$(e.missing)} 项` : "—"}</strong>
    <small>${e.online ? `找不到文件 · 已检查 ${$(e.checked)} 项` : `馆藏中有 ${$(e.total)} 项`}</small>
    ${e.unreadable ? `<small>${$(e.unreadable)} 项读取失败，已跳过</small>` : ""}</article>`).join("")}</div>
    <div class="resourcecache"><div><span>可清理的缓存</span><b>${$(n.files)} 个</b><small>${t(n.bytes)}</small></div>
    <div><span>待移入回收站</span><b>${$(e.missing)} 项</b></div></div>
    ${r ? p(`将把找不到文件的 ${$(e.missing)} 项馆藏记录移入回收站，并清理 ${$(n.files)} 个闲置缓存。`, { label: "清理内容" }) : ""}
    <div class="resourceapplyrow geist-fieldset-footer" data-geist-fieldset-footer>${r ? "<button class=\"geist-button primary\" type=\"button\" id=\"resourceApply\">清理失效记录与缓存</button>" : "<p class=\"resourcesyncok\">已检查可访问的来源，没有待清理的记录或缓存。</p>"}</div></div>`;
}
//#endregion
//#region src/jav-artwork.ts
function hr(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function gr(e) {
	return {
		javLayout: hr(e.javLayout),
		javImage: _r(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function _r(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function vr(e, t) {
	return e.is_jav && e.code && e.has_cover && (_r(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function yr(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (_r(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.removeAttribute("style"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var br = {
	"library-processing": {
		load: Pn,
		component: Fn
	},
	scraping: {
		load: An,
		component: Nn
	},
	"quality-goals": {
		load: Tn,
		component: Dn
	},
	configuration: {
		load: kt,
		component: It
	}
}, xr = () => Object.keys(br), Sr = /* @__PURE__ */ new Map();
async function Cr(e, t, n, r = {}) {
	let i = br[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	wr(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	Sr.set(t, a);
	let o;
	try {
		o = {
			data: await i.load(n, a.controller.signal),
			error: ""
		};
	} catch (e) {
		if (a.controller.signal.aborted) return;
		o = {
			data: null,
			error: z(e)
		};
	}
	if (Sr.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		Sr.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	Oe(oe(i.component, s), t);
}
function wr(e) {
	let t = Sr.get(e);
	t && (t.controller.abort(), Sr.delete(e), t.painted && Oe(null, e));
}
//#endregion
export { dr as TASTE_GUIDE_KEY, je as boundedPreference, rr as catalogEmptyHtml, nr as catalogSuggestions, lr as cleanupSkeletonHtml, sr as cloudLocations, cr as cloudPreferenceLocations, Un as createReviewSelection, Ie as distributionChart, tr as emptyCatalogLayout, $n as entitySkeletonHtml, kn as followJobProgress, Vn as identityEvidenceHtml, xr as islandNames, vr as javImageKind, Fe as jobProgressHtml, Zn as matchesFaceSource, Cr as mountIsland, Ne as mountNumberSetting, Qn as nativeImageFit, _r as normalizeJavImage, hr as normalizeJavLayout, gr as normalizeJavPreferences, ke as preferredDirection, Re as radarChart, Le as rankedChart, Rn as refreshStore, mr as resourceScanHtml, Bn as reviewImageHtml, ir as sidebarHasCatalogContent, Be as sidebarSectionHtml, or as sidebarTagCounts, Pe as statCardBody, Ln as storeNames, yr as syncJavImages, Me as syncNumberSetting, ar as syncSidebarSurface, ur as tasteHistoryGuideHtml, Ue as transitionTheme, wr as unmountIsland, Wn as updateReviewSticky, On as watchJob, Hn as wireReviewPictures, Xn as wireReviewSelection, Ve as wireSidebarGroups, fr as wireTasteHistoryGuide };
