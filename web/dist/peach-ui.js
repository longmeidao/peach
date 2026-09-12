import { LOC as e, esc as t, fmtDur as n, fmtSize as r, icon as i, requestErrorMessage as a, siteMarkUrl as o } from "/js/core.js";
import { MEDIA_SOURCE_ICONS as s, attachOverlayScrollbar as c, checkboxHtml as l, collectionSummaryHtml as u, confirmModal as d, emptyStateHtml as f, fieldsetTitle as p, loadingDotsHtml as m, moveGlidePane as h, noteHtml as g, progressHtml as _, projectBannerHtml as v, selectFieldHtml as y, selectOptionIconHtml as b, setActionBusy as x, wireCollapse as S, wireSelectField as C } from "/js/ui-components.js";
//#region node_modules/preact/dist/preact.module.js
var w, T, E, D, O, k, A, ee, te, j, M, ne, N, re, ie, ae = {}, oe = [], se = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, ce = Array.isArray;
function P(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function le(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function ue(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? w.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return de(e, o, r, i, null);
}
function de(e, t, n, r, i) {
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
		__v: i ?? ++E,
		__i: -1,
		__u: 0
	};
	return i == null && T.vnode != null && T.vnode(a), a;
}
function F(e) {
	return e.children;
}
function fe(e, t) {
	this.props = e, this.context = t;
}
function pe(e, t) {
	if (t == null) return e.__ ? pe(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? pe(e) : null;
}
function me(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = P({}, t);
		a.__v = t.__v + 1, T.vnode && T.vnode(a), Te(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? pe(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, De(r, a, i), t.__e = t.__ = null, a.__e != n && he(a);
	}
}
function he(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), he(e);
}
function ge(e) {
	(!e.__d && (e.__d = !0) && O.push(e) && !_e.__r++ || k != T.debounceRendering) && ((k = T.debounceRendering) || A)(_e);
}
function _e() {
	try {
		for (var e, t = 1; O.length;) O.length > t && O.sort(ee), e = O.shift(), t = O.length, me(e);
	} finally {
		O.length = _e.__r = 0;
	}
}
function ve(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || oe, v = t.length;
	for (c = ye(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || ae, p.__i = d, g = Te(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && Ae(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = be(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function ye(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = de(null, o, null, null, null) : ce(o) ? o = e.__k[a] = de(F, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = de(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = xe(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = pe(s)), je(s, s));
	return r;
}
function be(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = be(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = pe(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function xe(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function Se(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || se.test(t) ? n : n + "px";
}
function Ce(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || Se(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || Se(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(ne, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[M] = r[M] : (n[M] = N, e.addEventListener(t, a ? ie : re, a)) : e.removeEventListener(t, a ? ie : re, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function we(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[j] == null) t[j] = N++;
			else if (t[j] < n[M]) return;
			return n(T.event ? T.event(t) : t);
		}
	};
}
function Te(e, t, n, r, i, a, o, s, c, l) {
	var u, d, f, p, m, h, g, _, v, y, b, x, S, C, w, E, D = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (u = T.__b) && u(t);
	n: if (typeof D == "function") {
		d = o.length;
		try {
			if (v = t.props, y = D.prototype && D.prototype.render, b = (u = D.contextType) && r[u.__c], x = u ? b ? b.props.value : u.__ : r, n.__c ? _ = (f = t.__c = n.__c).__ = f.__E : (y ? t.__c = f = new D(v, x) : (t.__c = f = new fe(v, x), f.constructor = D, f.render = Me), b && b.sub(f), f.state || (f.state = {}), f.__n = r, p = f.__d = !0, f.__h = [], f._sb = []), y && f.__s == null && (f.__s = f.state), y && D.getDerivedStateFromProps != null && (f.__s == f.state && (f.__s = P({}, f.__s)), P(f.__s, D.getDerivedStateFromProps(v, f.__s))), m = f.props, h = f.state, f.__v = t, p) y && D.getDerivedStateFromProps == null && f.componentWillMount != null && f.componentWillMount(), y && f.componentDidMount != null && f.__h.push(f.componentDidMount);
			else {
				if (y && D.getDerivedStateFromProps == null && v !== m && f.componentWillReceiveProps != null && f.componentWillReceiveProps(v, x), t.__v == n.__v || !f.__e && f.shouldComponentUpdate != null && !1 === f.shouldComponentUpdate(v, f.__s, x)) {
					t.__v != n.__v && (f.props = v, f.state = f.__s, f.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), oe.push.apply(f.__h, f._sb), f._sb = [], f.__h.length && o.push(f), s = pe(n);
					break n;
				}
				f.componentWillUpdate != null && f.componentWillUpdate(v, f.__s, x), y && f.componentDidUpdate != null && f.__h.push(function() {
					f.componentDidUpdate(m, h, g);
				});
			}
			if (f.context = x, f.props = v, f.__P = e, f.__e = !1, S = T.__r, C = 0, y) f.state = f.__s, f.__d = !1, S && S(t), u = f.render(f.props, f.state, f.context), oe.push.apply(f.__h, f._sb), f._sb = [];
			else do
				f.__d = !1, S && S(t), u = f.render(f.props, f.state, f.context), f.state = f.__s;
			while (f.__d && ++C < 25);
			f.state = f.__s, f.getChildContext != null && (r = P(P({}, r), f.getChildContext())), y && !p && f.getSnapshotBeforeUpdate != null && (g = f.getSnapshotBeforeUpdate(m, h)), w = u != null && u.type === F && u.key == null ? Oe(u.props.children) : u, s = ve(e, ce(w) ? w : [w], t, n, r, i, a, o, s, c, l), f.base = t.__e, t.__u &= -161, f.__h.length && o.push(f), _ && (f.__E = f.__ = null);
		} catch (e) {
			if (o.length = d, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (E = a.length; E--;) le(a[E]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || Ee(t), T.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = ke(n.__e, t, n, r, i, a, o, c, l);
	return (u = T.diffed) && u(t), 128 & t.__u ? void 0 : s;
}
function Ee(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(Ee));
}
function De(e, t, n) {
	for (var r = 0; r < n.length; r++) Ae(n[r], n[++r], n[++r]);
	T.__c && T.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			T.__e(e, t.__v);
		}
	});
}
function Oe(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : ce(e) ? e.map(Oe) : e.constructor === void 0 ? P({}, e) : null;
}
function ke(e, t, n, r, i, a, o, s, c) {
	var l, u, d, f, p, m, h, g = n.props || ae, _ = t.props, v = t.type;
	if (v == "svg" ? i = "http://www.w3.org/2000/svg" : v == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (l = 0; l < a.length; l++) if ((p = a[l]) && "setAttribute" in p == !!v && (v ? p.localName == v : p.nodeType == 3)) {
			e = p, a[l] = null;
			break;
		}
	}
	if (e == null) {
		if (v == null) return document.createTextNode(_);
		e = document.createElementNS(i, v, _.is && _), s &&= (T.__m && T.__m(t, a), !1), a = null;
	}
	if (v == null) g === _ || s && e.data == _ || (e.data = _);
	else {
		if (a = v == "textarea" && _.defaultValue != null ? null : a && w.call(e.childNodes), !s && a != null) for (g = {}, l = 0; l < e.attributes.length; l++) g[(p = e.attributes[l]).name] = p.value;
		for (l in g) p = g[l], l == "dangerouslySetInnerHTML" ? d = p : l == "children" || l in _ || l == "value" && "defaultValue" in _ || l == "checked" && "defaultChecked" in _ || Ce(e, l, null, p, i);
		for (l in _) p = _[l], l == "children" ? f = p : l == "dangerouslySetInnerHTML" ? u = p : l == "value" ? m = p : l == "checked" ? h = p : s && typeof p != "function" || g[l] === p || Ce(e, l, p, g[l], i);
		if (u) s || d && (u.__html == d.__html || u.__html == e.innerHTML) || (e.innerHTML = u.__html), t.__k = [];
		else if (d && (e.innerHTML = ""), ve(t.type == "template" ? e.content : e, ce(f) ? f : [f], t, n, r, v == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && pe(n, 0), s, c), a != null) for (l = a.length; l--;) le(a[l]);
		s && v != "textarea" || (l = "value", v == "progress" && m == null ? e.removeAttribute("value") : m != null && (m !== e[l] || v == "progress" && !m || v == "option" && m != g[l]) && Ce(e, l, m, g[l], i), l = "checked", h != null && h != e[l] && Ce(e, l, h, g[l], i));
	}
	return e;
}
function Ae(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		T.__e(e, n);
	}
}
function je(e, t, n) {
	var r, i;
	if (T.unmount && T.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || Ae(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			T.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && je(r[i], t, n || typeof e.type != "function");
	n || le(e.__e), e.__c = e.__ = e.__e = void 0;
}
function Me(e, t, n) {
	return this.constructor(e, n);
}
function Ne(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), T.__ && T.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], Te(t, e = (!r && n || t).__k = ue(F, null, [e]), i || ae, ae, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? w.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), De(a, e, o), e.props.children = null;
}
w = oe.slice, T = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, E = 0, D = function(e) {
	return e != null && e.constructor === void 0;
}, fe.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = P({}, this.state);
	typeof e == "function" && (e = e(P({}, n), this.props)), e && P(n, e), e != null && this.__v && (t && this._sb.push(t), ge(this));
}, fe.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), ge(this));
}, fe.prototype.render = F, O = [], A = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, ee = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, _e.__r = 0, te = Math.random().toString(8), j = "__d" + te, M = "__a" + te, ne = /(PointerCapture)$|Capture$/i, N = 0, re = we(!1), ie = we(!0);
//#endregion
//#region src/sort-preferences.ts
function Pe(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/number-setting.ts
var Fe = {
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
function Ie(e, t, n, r) {
	return Number.isInteger(e) && e >= t && e <= n ? e : r;
}
function Le(e, t, n) {
	let r = e.querySelector("input[type=number]"), i = e.querySelector("[role=switch]"), a = e.querySelector(".board-number-fields");
	r && (r.disabled = n, t !== null && t > 0 && (r.value = String(t))), i && (i.disabled = n, t !== null && (i.checked = t > 0)), a && t !== null && (a.hidden = t === 0);
}
function Re(e, t, n, r, i) {
	let a = Fe[t];
	if (!a) return !1;
	let { min: o, max: s, unit: c, optional: l, fallback: u } = a, d = `peach.number.${t}`, f = Ie(Number(localStorage.getItem(d)), o, s, r > 0 ? r : u), p = document.createElement("div");
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
var I = (e) => String(e ?? "").replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function ze(e, t, n, r = "chart-no-axes-combined") {
	return `<span class="board-stat-label"><span class="board-stat-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><use href="#i-${/^[a-z0-9-]+$/.test(r) ? r : "database"}"/></svg></span>${I(e)}</span><b class="board-stat-value">${I(t)}</b><small class="board-stat-footer">${I(n || "当前记录")}</small>`;
}
function Be(e, t, n) {
	if (!Number.isFinite(n) || n <= 0) return "";
	let r = Math.max(0, Math.min(n, Number.isFinite(t) ? t : 0)), i = r / n * 100;
	return `<div class="board-job-progress" role="progressbar" aria-label="${I(e)}" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${r}"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle class="board-job-track" cx="18" cy="18" r="15"/><circle class="board-job-fill" cx="18" cy="18" r="15" pathLength="100" stroke-dasharray="${i} ${100 - i}" transform="rotate(-90 18 18)"/></svg><span>${I(e)}<small>${Math.round(i)}%</small></span></div>`;
}
function Ve(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0), r = n.reduce((e, t) => e + t.score, 0);
	if (!r) return "";
	let i = 0, a = n.map((e, t) => {
		let n = e.score / r * 100, a = `<circle cx="100" cy="100" r="72" pathLength="100" fill="none" stroke="var(--chart-${t % 4})" stroke-width="22" stroke-dasharray="${n} ${100 - n}" stroke-dashoffset="${-i}"><title>${I(e.name)}：${e.score.toLocaleString()}</title></circle>`;
		return i += n, a;
	}).join("");
	return `<svg class="board-distribution" viewBox="0 0 200 200" role="img" aria-label="${I(t)}"><g transform="rotate(-90 100 100)">${a}</g><text x="100" y="100" text-anchor="middle" dominant-baseline="middle">${I(t)}</text></svg>`;
}
function He(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0).slice().sort((e, t) => t.score - e.score).slice(0, 8);
	if (!n.length) return "";
	let r = n[0].score, i = n.map((e) => `<li><span class="board-rank-fill" style="width:${(e.score / r * 100).toFixed(2)}%"></span><span>${I(e.name)}</span><b>${e.score.toLocaleString()}</b></li>`).join("");
	return `<ol class="board-ranked-chart" aria-label="${I(t)}">${i}</ol>`;
}
function Ue(e, t) {
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
		return `<text x="${n}" y="${r}" text-anchor="${n < 145 ? "end" : n > 175 ? "start" : "middle"}">${I(e.name)}</text>`;
	}).join("");
	return `<svg class="board-radar" viewBox="0 0 320 280" role="img" aria-label="${I(t)}"><title>${I(n.map((e) => `${e.name} ${e.score}`).join("，"))}</title>${s}<polygon points="${o((e) => n[e].score / r * 100)}" class="board-radar-value"/>${c}</svg>`;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var We, L, Ge, Ke, qe = 0, Je = [], R = T, Ye = R.__b, Xe = R.__r, Ze = R.diffed, Qe = R.__c, $e = R.unmount, et = R.__;
function tt(e, t) {
	R.__h && R.__h(L, e, qe || t), qe = 0;
	var n = L.__H || (L.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function z(e) {
	return qe = 1, nt(ut, e);
}
function nt(e, t, n) {
	var r = tt(We++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : ut(void 0, t), function(e) {
		var t = r.__N ? r.__N[0] : r.__[0], n = r.t(t, e);
		t !== n && (r.__N = [n, r.__[1]], r.__c.setState({}));
	}], r.__c = L, !L.__f)) {
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
		L.__f = !0;
		var a = L.shouldComponentUpdate, o = L.componentWillUpdate;
		L.componentWillUpdate = function(e, t, n) {
			if (this.__e) {
				var r = a;
				a = void 0, i(e, t, n), a = r;
			}
			o && o.call(this, e, t, n);
		}, L.shouldComponentUpdate = i;
	}
	return r.__N || r.__;
}
function B(e, t) {
	var n = tt(We++, 3);
	!R.__s && lt(n.__H, t) && (n.__ = e, n.u = t, L.__H.__h.push(n));
}
function V(e, t) {
	var n = tt(We++, 4);
	!R.__s && lt(n.__H, t) && (n.__ = e, n.u = t, L.__h.push(n));
}
function H(e) {
	return qe = 5, rt(function() {
		return { current: e };
	}, []);
}
function rt(e, t) {
	var n = tt(We++, 7);
	return lt(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function it() {
	for (var e; e = Je.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(st), t.__h.some(ct), t.__h = [];
		} catch (n) {
			t.__h = [], R.__e(n, e.__v);
		}
	}
}
R.__b = function(e) {
	L = null, Ye && Ye(e);
}, R.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), et && et(e, t);
}, R.__r = function(e) {
	Xe && Xe(e), We = 0;
	var t = (L = e.__c).__H;
	t && (Ge === L ? (t.__h = [], L.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(st), t.__h.some(ct), t.__h = [], We = 0)), Ge = L;
}, R.diffed = function(e) {
	Ze && Ze(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Je.push(t) !== 1 && Ke === R.requestAnimationFrame || ((Ke = R.requestAnimationFrame) || ot)(it)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), Ge = L = null;
}, R.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(st), e.__h = e.__h.filter(function(e) {
				return !e.__ || ct(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], R.__e(n, e.__v);
		}
	}), Qe && Qe(e, t);
}, R.unmount = function(e) {
	$e && $e(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			st(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && R.__e(t, n.__v));
};
var at = typeof requestAnimationFrame == "function";
function ot(e) {
	var t, n = function() {
		clearTimeout(r), at && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	at && (t = requestAnimationFrame(n));
}
function st(e) {
	var t = L, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), L = t;
}
function ct(e) {
	var t = L;
	e.__c = e.__(), L = t;
}
function lt(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function ut(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region src/api.ts
var dt = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(a(e, t)), this.name = "ApiError", this.status = t, this.body = n;
	}
}, ft = (e) => {
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
}, U = (e) => a(e);
async function W(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new dt(ft(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function G(e, t, n = "POST", r) {
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
	if (!i.ok) throw new dt(ft(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region src/jobs.ts
function pt(e, t = 0, n = 0) {
	return n > 0 ? Be(e, t, n) : m(e);
}
async function mt(e) {
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
function ht(e) {
	let t = e.note || ((e) => g(e, {
		label: "任务状态",
		variant: "error"
	})), n = e.loading || m, r = e.progress || ((e, t, n) => pt(n || `已处理 ${e} / ${t}`, e, t)), i = e.container || ((e) => `<section class="followtask" data-geist-fieldset aria-label="任务进度"><div class="geist-fieldset-content">${e}</div></section>`), a = document.createElement("div");
	e.host.hidden = !0, a.dataset.followJob = "", a.setAttribute("aria-live", "polite"), e.host.prepend(a);
	let o = e.storageKey || "peach-follow-job", s = sessionStorage.getItem(o) || void 0, c = !1;
	mt({
		read: e.read,
		active: () => !c && e.active() && a.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (l) => {
			let u = l.status === "running";
			if (e.host.hidden = !u, e.busy(u), u) {
				s = l.job_id, s && sessionStorage.setItem(o, s);
				let t = l.current, c = (t?.attempt || 1) > 1 ? ` · 第 ${t?.attempt}/${t?.max_attempts} 次尝试${t?.retry_in ? `，${t.retry_in} 秒后重试` : ""}` : "", u = (l.message || (e.title ? e.title + (l.total ? `：已完成 ${l.checked || 0}/${l.total}` : "") : "") || (l.total ? `${l.older ? "抓取历史" : "检查更新"}：已完成 ${l.checked || 0}/${l.total} 个来源` : "正在准备检查任务…")) + (t ? ` · ${t.label || t.provider || ""}${c}` : ""), d = (l.total || 0) > 0 ? r(l.checked || 0, l.total, u) : n(u);
				a.innerHTML = i(d);
			} else if (s && s === l.job_id) s = void 0, c = !0, e.host.hidden = l.status !== "failed", sessionStorage.removeItem(o), a.innerHTML = l.status === "failed" ? t(l.error || "检查失败") : "", e.complete(l);
			else {
				if (s && l.status === "idle") {
					e.host.hidden = !1, a.innerHTML = t("任务状态已失效，请重新发起任务"), sessionStorage.removeItem(o), c = !0;
					return;
				}
				a.innerHTML = "";
			}
		},
		disconnected: () => {
			e.host.hidden = !1, a.innerHTML = t("暂时无法读取进度，正在重新连接…");
		}
	});
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var gt = 0;
Array.isArray;
function K(e, t, n, r, i, a) {
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
		__v: --gt,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (o = e.defaultProps)) for (s in o) c[s] === void 0 && (c[s] = o[s]);
	return T.vnode && T.vnode(l), l;
}
//#endregion
//#region src/link-button.tsx
function _t({ href: e, children: t }) {
	return /* @__PURE__ */ K("a", {
		class: "board-link-button",
		href: e,
		children: [/* @__PURE__ */ K("span", { children: t }), /* @__PURE__ */ K("svg", {
			viewBox: "0 0 24 24",
			"aria-hidden": "true",
			children: /* @__PURE__ */ K("use", { href: "#i-arrow-up" })
		})]
	});
}
//#endregion
//#region src/islands/library-processing.tsx
var vt = (e, t) => W("/api/library-processing", t), yt = {
	reading_local: "读取本地资料",
	querying_metadata: "查询外部资料",
	fetching_cover: "采集缺失封面",
	writing_candidates: "保存资料候选"
};
function bt(e) {
	let t = yt[e.current_action || ""] || e.stage || "正在处理", n = e.waited_seconds ? ` · 已等待 ${e.waited_seconds} 秒` : "";
	return e.current_asset_name ? `当前：${e.current_asset_name} · ${t}${n}` : t + n;
}
function xt({ data: e, error: t, toast: n, onComplete: r, mode: i, monitor: a, preview: o }) {
	let [s, c] = z(e || { status: "idle" }), [l, u] = z(t), [d, f] = z(!1), [m, h] = z(!1), _ = H(new AbortController()), y = H(0), b = H(s.status), S = H(null), C = d || s.status === "running";
	V(() => x(S.current, C), [C]);
	async function w() {
		let e = ++y.current;
		await mt({
			read: (e) => W("/api/library-processing", e),
			active: () => !_.current.signal.aborted && y.current === e,
			keepWatching: i === "notice" || !!a,
			render: (e) => {
				c(e), u(""), e.status === "complete" && b.current === "running" && i !== "notice" && (h(!0), n("已完成扫描与资料采集")), b.current === "running" && (e.status === "complete" || e.status === "failed") && r?.(), b.current = e.status;
			},
			disconnected: () => u("连接中断，正在重新读取处理进度")
		});
	}
	B(() => (!o && (s.status === "running" || i === "notice" || a) && w(), () => _.current.abort()), []);
	async function T(e) {
		if (!(C || o)) {
			f(!0), u(""), h(!1);
			try {
				let t = await G("/api/library-processing", e, "POST", _.current.signal);
				if (_.current.signal.aborted) return;
				b.current = t.status, c(t), f(!1), await w();
			} catch (e) {
				_.current.signal.aborted || (u(U(e)), f(!1));
			}
		}
	}
	let E = () => void T({}), D = () => {
		!s.job_id || !s.retryable_asset_ids?.length || T({
			job_id: s.job_id,
			retry: s.retryable_asset_ids
		});
	};
	if (i === "notice") {
		if (!l && s.status !== "running" && s.status !== "failed") return null;
		let e = l || (s.status === "failed" ? "扫描与资料采集未完成" : bt(s) + (s.total ? ` · ${s.checked || 0} / ${s.total}` : ""));
		return /* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: v(e, {
			variant: s.status === "failed" ? "error" : l || s.stalled ? "warning" : "gray",
			href: "/data-cleanup#libraryProcessing",
			label: l || s.status === "failed" ? "查看并处理" : "查看进度",
			value: s.checked || 0,
			...s.status === "running" && s.total !== void 0 ? { max: s.total } : {}
		}) } });
	}
	let O = s.issue_preview || [], k = s.status === "failed" && !!s.retryable_asset_ids?.length, A = s.status === "failed" && O.length ? {
		label: s.issues_truncated ? `问题清单：共 ${s.issue_count || 0} 项，展开查看前 ${O.length} 项` : `问题清单：共 ${s.issue_count || 0} 项`,
		items: O.map((e) => ({
			label: e.title || (e.asset_id ? `视频 ${e.asset_id}` : "媒体来源"),
			href: e.asset_id ? `/item/${e.asset_id}` : "",
			note: e.message,
			hint: e.path || ""
		})),
		footnote: s.issues_log ? `完整记录：${s.issues_log}` : ""
	} : null;
	return /* @__PURE__ */ K(F, { children: [/* @__PURE__ */ K("section", {
		class: "cleanupfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "cleanupScrapingTitle",
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content library-processing",
			children: [
				/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: p("cleanupScrapingTitle", "扫描与采集") } }),
				/* @__PURE__ */ K("p", { children: "扫描媒体文件夹，导入已有资料，采集缺失信息。两段也可以分开跑：新盘刚接上时先只扫描，几万个文件登记完就能用；采集被网络拖住时只重跑采集，不必再扫一遍磁盘。" }),
				s.status === "running" && /* @__PURE__ */ K("div", {
					"aria-live": "polite",
					dangerouslySetInnerHTML: { __html: pt(s.total ? `${bt(s)} · ${s.checked || 0} / ${s.total} 个视频` : bt(s), s.checked, s.total) }
				})
			]
		}), /* @__PURE__ */ K("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [
				/* @__PURE__ */ K(_t, {
					href: "/scraping",
					children: "采集来源"
				}),
				!!s.candidates && /* @__PURE__ */ K(_t, {
					href: "/review",
					children: "复核资料"
				}),
				(s.status !== "failed" || !k) && /* @__PURE__ */ K("div", {
					class: "board-button-group",
					role: "group",
					"aria-label": "扫描与采集",
					children: [
						/* @__PURE__ */ K("button", {
							type: "button",
							class: "geist-button",
							onClick: () => void T({ stage: "scan" }),
							children: "只扫描"
						}),
						/* @__PURE__ */ K("button", {
							type: "button",
							class: "geist-button",
							onClick: () => void T({ stage: "collect" }),
							children: "只采集"
						}),
						/* @__PURE__ */ K("button", {
							ref: S,
							type: "button",
							class: "geist-button primary",
							onClick: E,
							children: "扫描并补全资料"
						})
					]
				})
			]
		})]
	}), /* @__PURE__ */ K("div", {
		class: "library-processing-outcome",
		"aria-live": "polite",
		children: [
			s.status === "running" && s.stalled && /* @__PURE__ */ K("div", {
				class: "library-processing-stalled",
				dangerouslySetInnerHTML: { __html: g("这个项目处理时间较长，暂时没有新进展。可以继续等待，或在任务结束后重试未完成项。", {
					variant: "warning",
					label: "处理较慢",
					filled: !0
				}) }
			}),
			(l || s.status === "failed") && /* @__PURE__ */ K("div", {
				role: "alert",
				onClick: (e) => {
					e.target.closest("[data-note-action]") && D();
				},
				dangerouslySetInnerHTML: { __html: g(l || s.error || "处理未完成，请重试", {
					variant: "error",
					filled: !0,
					actionLabel: k ? "重试未完成项" : "",
					details: A
				}) }
			}),
			m && /* @__PURE__ */ K("div", {
				class: "library-processing-result",
				dangerouslySetInnerHTML: { __html: g(`已扫描 ${s.scanned || 0} 个文件，识别 ${s.identified || 0} 个番号，整理 ${s.candidates || 0} 组资料候选。`, {
					variant: "success",
					label: "处理完成"
				}) }
			})
		]
	})] });
}
//#endregion
//#region src/management.ts
function St(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function Ct(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function wt() {
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
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><a class="geist-button" href="/scraping">采集来源</a><button type="button" class="geist-button primary" disabled>扫描并补全资料</button></footer>
      </section>
      <section class="cleanupfieldset cleanupemptyfolders" data-geist-fieldset aria-labelledby="cleanup-loading-empty">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-empty">空文件夹</h3>
          <strong>${t}</strong><p class="cleanupmeta">${t}</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" disabled><svg aria-hidden="true"><use href="#i-scan-search"></use></svg><span>扫描空文件夹</span></button></footer>
      </section></div></div>`;
}
function Tt(e, t = !1, n = !1) {
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
var Et = "peach-taste-guide-dismissed";
function Dt(e, t) {
	S(e, ".taste-history-guide", "taste-guide-collapse");
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(Et, "1"), n.remove();
	});
}
//#endregion
//#region src/board-state-preview.tsx
var Ot = [
	["idle", "待开始"],
	["loading", "页面加载"],
	["preparing", "准备任务"],
	["running", "任务进行中"],
	["retrying", "等待重试"],
	["disconnected", "失去连接"],
	["reconnected", "恢复连接"],
	["failed", "任务失败"],
	["complete", "任务完成"],
	["expired", "状态已失效"],
	["paused", "来源已暂停"]
], q = ({ html: e }) => /* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: e } });
function kt() {
	let [e, t] = z("running"), [n, r] = z(0), [i, a] = z(document.documentElement.dataset.theme === "dark"), [o, s] = z(38), c = {
		status: e === "failed" ? "failed" : [
			"running",
			"preparing",
			"disconnected",
			"retrying",
			"reconnected"
		].includes(e) ? "running" : "idle",
		stage: e === "preparing" ? "正在准备扫描" : e === "retrying" ? "等待来源响应 · 8 秒后重试" : "正在整理资料",
		checked: o,
		...e === "preparing" ? {} : { total: 100 },
		error: e === "failed" ? "来源暂时不可用，请重试未完成项" : "",
		issue_count: +(e === "failed"),
		issue_preview: e === "failed" ? [{
			asset_id: null,
			title: "本地磁盘",
			path: "R:\\Media",
			message: "来源连接超时"
		}] : [],
		issues_log: e === "failed" ? "peach-data\\state\\library-processing-preview.issues.jsonl" : "",
		retryable_asset_ids: e === "failed" ? [7] : []
	}, l = e === "disconnected" ? "连接中断，正在重新读取处理进度" : "";
	return /* @__PURE__ */ K("main", {
		class: "board-state-preview",
		children: [
			/* @__PURE__ */ K("header", { children: [/* @__PURE__ */ K("div", { children: [/* @__PURE__ */ K("h1", { children: "运行状态预览" }), /* @__PURE__ */ K("p", { children: "演示数据 · 不连接任务接口，不执行扫描或写入。" })] }), /* @__PURE__ */ K("button", {
				class: "geist-button",
				onClick: () => {
					document.documentElement.dataset.theme = i ? "light" : "dark", a(!i);
				},
				children: i ? "浅色" : "深色"
			})] }),
			/* @__PURE__ */ K("nav", {
				"aria-label": "演示状态",
				children: Ot.map(([i, a]) => /* @__PURE__ */ K("button", {
					class: "geist-button",
					"aria-pressed": e === i,
					onClick: () => {
						t(i), r(n + 1);
					},
					children: a
				}))
			}),
			/* @__PURE__ */ K("div", {
				class: "board-preview-tools",
				children: [/* @__PURE__ */ K("label", { children: [
					"任务进度 ",
					/* @__PURE__ */ K("input", {
						type: "range",
						min: "0",
						max: "100",
						value: o,
						onInput: (e) => s(Number(e.currentTarget.value))
					}),
					/* @__PURE__ */ K("output", { children: [o, "%"] })
				] }), /* @__PURE__ */ K("button", {
					class: "geist-button",
					onClick: () => r(n + 1),
					children: "重播状态"
				})]
			}),
			/* @__PURE__ */ K("section", {
				"aria-label": "页面横幅",
				children: [
					/* @__PURE__ */ K("h2", { children: "全局任务横幅" }),
					/* @__PURE__ */ K(xt, {
						data: c,
						error: l,
						mode: "notice",
						preview: !0,
						toast: () => {}
					}, `banner-${e}-${n}-${o}`),
					![
						"running",
						"preparing",
						"disconnected",
						"retrying",
						"reconnected",
						"failed"
					].includes(e) && /* @__PURE__ */ K("p", { children: "此状态不常驻全局横幅。" })
				]
			}),
			/* @__PURE__ */ K("section", { children: [
				/* @__PURE__ */ K("h2", { children: "数据管理 · 扫描与采集" }),
				e === "loading" ? /* @__PURE__ */ K(q, { html: wt() }) : /* @__PURE__ */ K("div", {
					class: "cleanupgrid",
					children: /* @__PURE__ */ K("div", {
						id: "libraryProcessing",
						class: "cleanupscraping",
						children: /* @__PURE__ */ K(xt, {
							data: c,
							error: l,
							preview: !0,
							toast: () => {}
						}, `${e}-${n}-${o}`)
					})
				}),
				e === "complete" && /* @__PURE__ */ K(q, { html: g("已完成扫描与资料采集", {
					variant: "success",
					label: "任务完成"
				}) }),
				e === "expired" && /* @__PURE__ */ K(q, { html: g("任务状态已失效，请重新发起任务", { variant: "warning" }) }),
				e === "paused" && /* @__PURE__ */ K("span", {
					class: "sbadge paused",
					children: "已暂停"
				})
			] }),
			/* @__PURE__ */ K("section", { children: [/* @__PURE__ */ K("h2", { children: "关注检查与资源同步" }), /* @__PURE__ */ K("div", {
				class: "board-preview-grid",
				children: [/* @__PURE__ */ K("article", { children: [/* @__PURE__ */ K("h3", { children: "检查更新" }), /* @__PURE__ */ K(q, { html: e === "disconnected" ? g("暂时无法读取进度，正在重新连接…", { label: "任务状态" }) : e === "failed" ? g("检查失败：来源连接超时", {
					variant: "error",
					actionLabel: "重试"
				}) : e === "running" || e === "retrying" || e === "reconnected" ? Be(`${e === "retrying" ? "第 2/3 次尝试，8 秒后重试 · " : ""}已完成 ${o}/100 个来源`, o, 100) : e === "preparing" ? m("正在准备检查任务…") : g(e === "complete" ? "已完成检查" : e === "paused" ? "已暂停自动检查" : e === "expired" ? "任务状态已失效，请重新发起任务" : "等待开始", { variant: e === "complete" ? "success" : "secondary" }) })] }), /* @__PURE__ */ K("article", { children: [
					/* @__PURE__ */ K("h3", { children: "连接与恢复" }),
					/* @__PURE__ */ K(q, { html: v(e === "disconnected" ? "暂时无法连接服务器，正在重连" : e === "reconnected" ? "连接已恢复，继续读取任务进度" : "连接正常", {
						variant: e === "disconnected" ? "warning" : "gray",
						href: "#",
						label: "查看状态"
					}) }),
					/* @__PURE__ */ K("p", { children: "失去连接只影响进度读取；恢复连接后继续展示任务状态。" })
				] })]
			})] }),
			/* @__PURE__ */ K("section", { children: [/* @__PURE__ */ K("h2", { children: "错误与加载状态一览" }), /* @__PURE__ */ K("div", {
				class: "board-preview-grid",
				children: [
					/* @__PURE__ */ K("article", { children: [/* @__PURE__ */ K("h3", { children: "读取失败" }), /* @__PURE__ */ K(q, { html: g("无法读取状态，请重试", {
						variant: "error",
						actionLabel: "重试"
					}) })] }),
					/* @__PURE__ */ K("article", { children: [/* @__PURE__ */ K("h3", { children: "来源离线" }), /* @__PURE__ */ K(q, { html: g("媒体来源离线，请检查挂载状态", { variant: "warning" }) })] }),
					/* @__PURE__ */ K("article", { children: [/* @__PURE__ */ K("h3", { children: "没有待处理内容" }), /* @__PURE__ */ K(q, { html: g("没有待处理内容", { variant: "secondary" }) })] }),
					/* @__PURE__ */ K("article", { children: [/* @__PURE__ */ K("h3", { children: "等待响应" }), /* @__PURE__ */ K(q, { html: m("正在读取来源状态") })] })
				]
			})] })
		]
	});
}
function At(e) {
	Ne(ue(kt, {}), e);
}
//#endregion
//#region src/board-controls.ts
function jt(e) {
	let t = Number(e.min) || 0, n = Number(e.max) || 100, r = Number(e.value), i = n > t ? Math.max(0, Math.min(100, (r - t) / (n - t) * 100)) : 0;
	e.style.setProperty("--board-range-value", `${i}%`);
	let a = e.closest(".dual-range");
	if (!a) return;
	let o = e.id === "durMax" ? "max" : "min", s = a.querySelector(`[data-range-end="${o}"]`);
	s || (s = document.createElement("output"), s.className = "board-range-tip", s.dataset.rangeEnd = o, s.setAttribute("aria-hidden", "true"), a.append(s)), s.textContent = r >= n && o === "max" ? "不限" : `${r} 分钟`, s.style.left = `${i}%`, s.style.setProperty("--range-tip-shift", "0px");
	let c = a.getBoundingClientRect(), l = s.getBoundingClientRect(), u = l.right > c.right ? c.right - l.right : l.left < c.left ? c.left - l.left : 0;
	u && s.style.setProperty("--range-tip-shift", `${Math.round(u)}px`), a.querySelectorAll(".board-range-tip").forEach((e) => e.toggleAttribute("data-range-active", e === s));
}
function Mt() {
	let e = (e) => {
		e.querySelectorAll("input[type=range]").forEach(jt), It(e), Pt(e), Lt(e);
	};
	e(document), new MutationObserver((t) => {
		for (let n of t) for (let t of n.addedNodes) t instanceof Element && (t.matches("input[type=range]") && jt(t), e(t));
	}).observe(document.body, {
		subtree: !0,
		childList: !0
	}), document.addEventListener("input", (e) => {
		e.target instanceof HTMLInputElement && e.target.type === "range" && jt(e.target);
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
var Nt = /* @__PURE__ */ new Map();
function Pt(e) {
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
			n(i), Nt.set(t, i);
		}, i = Nt.get(t);
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
var Ft = /* @__PURE__ */ new Map();
function It(e) {
	let t = ".iconswitch,.insightswitch,.insighttabs,.follow-workspace-switch", n = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && n.push(e), n.forEach((e) => {
		if (e.hasAttribute("data-board-segments") || e.closest("[data-skeleton]")) return;
		e.dataset.boardSegments = "true";
		let t = document.createElement("span");
		t.className = "board-segment-thumb", t.setAttribute("aria-hidden", "true"), e.prepend(t);
		let n = e.className + (e.getAttribute("aria-label") ?? ""), r = Ft.get(n) ?? null, i = () => {
			let i = e.querySelector("label:has(input:checked),button[aria-selected=true]");
			if (!i || !i.offsetWidth) return;
			let a = {
				x: i.offsetLeft,
				y: i.offsetTop,
				w: i.offsetWidth,
				h: i.offsetHeight
			};
			h(t, r, a, "x"), r = a, Ft.set(n, a);
		};
		e.addEventListener("change", i);
		let a = new MutationObserver(i);
		a.observe(e, {
			subtree: !0,
			attributes: !0,
			attributeFilter: ["aria-selected"]
		});
		let o = new ResizeObserver(() => {
			if (!e.isConnected) {
				o.disconnect(), a.disconnect();
				return;
			}
			i();
		});
		o.observe(e), i(), requestAnimationFrame(() => e.classList.add("board-segments-ready"));
	});
}
function Lt(e) {
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
function Rt(e) {
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
		};
		r.onclick = () => {
			let e = r.getAttribute("aria-expanded") !== "true";
			r.setAttribute("aria-expanded", String(e)), r.setAttribute("aria-label", e ? "收起排名" : "展开更多排名"), a();
		}, new ResizeObserver(i).observe(e), a();
	});
}
//#endregion
//#region node_modules/d3-array/src/max.js
function zt(e, t) {
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
function Bt(e, t) {
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
function Vt(e, t) {
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
function Ht(e, t) {
	return e.sourceLinks.length ? e.depth : t - 1;
}
//#endregion
//#region node_modules/d3-sankey/src/constant.js
function Ut(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-sankey/src/sankey.js
function Wt(e, t) {
	return Kt(e.source, t.source) || e.index - t.index;
}
function Gt(e, t) {
	return Kt(e.target, t.target) || e.index - t.index;
}
function Kt(e, t) {
	return e.y0 - t.y0;
}
function qt(e) {
	return e.value;
}
function Jt(e) {
	return e.index;
}
function Yt(e) {
	return e.nodes;
}
function Xt(e) {
	return e.links;
}
function Zt(e, t) {
	let n = e.get(t);
	if (!n) throw Error("missing: " + t);
	return n;
}
function Qt({ nodes: e }) {
	for (let t of e) {
		let e = t.y0, n = e;
		for (let n of t.sourceLinks) n.y0 = e + n.width / 2, e += n.width;
		for (let e of t.targetLinks) e.y1 = n + e.width / 2, n += e.width;
	}
}
function $t() {
	let e = 0, t = 0, n = 1, r = 1, i = 24, a = 8, o, s = Jt, c = Ht, l, u, d = Yt, f = Xt, p = 6;
	function m() {
		let e = {
			nodes: d.apply(null, arguments),
			links: f.apply(null, arguments)
		};
		return h(e), g(e), _(e), v(e), x(e), Qt(e), e;
	}
	m.update = function(e) {
		return Qt(e), e;
	}, m.nodeId = function(e) {
		return arguments.length ? (s = typeof e == "function" ? e : Ut(e), m) : s;
	}, m.nodeAlign = function(e) {
		return arguments.length ? (c = typeof e == "function" ? e : Ut(e), m) : c;
	}, m.nodeSort = function(e) {
		return arguments.length ? (l = e, m) : l;
	}, m.nodeWidth = function(e) {
		return arguments.length ? (i = +e, m) : i;
	}, m.nodePadding = function(e) {
		return arguments.length ? (a = o = +e, m) : a;
	}, m.nodes = function(e) {
		return arguments.length ? (d = typeof e == "function" ? e : Ut(e), m) : d;
	}, m.links = function(e) {
		return arguments.length ? (f = typeof e == "function" ? e : Ut(e), m) : f;
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
			typeof t != "object" && (t = r.source = Zt(n, t)), typeof i != "object" && (i = r.target = Zt(n, i)), t.sourceLinks.push(r), i.targetLinks.push(r);
		}
		if (u != null) for (let { sourceLinks: t, targetLinks: n } of e) t.sort(u), n.sort(u);
	}
	function g({ nodes: e }) {
		for (let t of e) t.value = t.fixedValue === void 0 ? Math.max(Vt(t.sourceLinks, qt), Vt(t.targetLinks, qt)) : t.fixedValue;
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
		let r = zt(t, (e) => e.depth) + 1, a = (n - e - i) / (r - 1), o = Array(r);
		for (let n of t) {
			let t = Math.max(0, Math.min(r - 1, Math.floor(c.call(null, n, r))));
			n.layer = t, n.x0 = e + t * a, n.x1 = n.x0 + i, o[t] ? o[t].push(n) : o[t] = [n];
		}
		if (l) for (let e of o) e.sort(l);
		return o;
	}
	function b(e) {
		let n = Bt(e, (e) => (r - t - (e.length - 1) * o) / Vt(e, qt));
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
		o = Math.min(a, (r - t) / (zt(n, (e) => e.length) - 1)), b(n);
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
			l === void 0 && i.sort(Kt), w(i, n);
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
			l === void 0 && i.sort(Kt), w(i, n);
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
			for (let { source: { sourceLinks: e } } of t) e.sort(Gt);
			for (let { target: { targetLinks: t } } of e) t.sort(Wt);
		}
	}
	function O(e) {
		if (u === void 0) for (let { sourceLinks: t, targetLinks: n } of e) t.sort(Gt), n.sort(Wt);
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
var en = Math.PI, tn = 2 * en, nn = 1e-6, rn = tn - nn;
function an() {
	this._x0 = this._y0 = this._x1 = this._y1 = null, this._ = "";
}
function on() {
	return new an();
}
an.prototype = on.prototype = {
	constructor: an,
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
		else if (d > nn) {
			if (!(Math.abs(u * s - c * l) > nn) || !i) this._ += "L" + (this._x1 = e) + "," + (this._y1 = t);
			else {
				var f = n - a, p = r - o, m = s * s + c * c, h = f * f + p * p, g = Math.sqrt(m), _ = Math.sqrt(d), v = i * Math.tan((en - Math.acos((m + d - h) / (2 * g * _))) / 2), y = v / _, b = v / g;
				Math.abs(y - 1) > nn && (this._ += "L" + (e + y * l) + "," + (t + y * u)), this._ += "A" + i + "," + i + ",0,0," + +(u * f > l * p) + "," + (this._x1 = e + b * s) + "," + (this._y1 = t + b * c);
			}
		}
	},
	arc: function(e, t, n, r, i, a) {
		e = +e, t = +t, n = +n, a = !!a;
		var o = n * Math.cos(r), s = n * Math.sin(r), c = e + o, l = t + s, u = 1 ^ a, d = a ? r - i : i - r;
		if (n < 0) throw Error("negative radius: " + n);
		this._x1 === null ? this._ += "M" + c + "," + l : (Math.abs(this._x1 - c) > nn || Math.abs(this._y1 - l) > nn) && (this._ += "L" + c + "," + l), n && (d < 0 && (d = d % tn + tn), d > rn ? this._ += "A" + n + "," + n + ",0,1," + u + "," + (e - o) + "," + (t - s) + "A" + n + "," + n + ",0,1," + u + "," + (this._x1 = c) + "," + (this._y1 = l) : d > nn && (this._ += "A" + n + "," + n + ",0," + +(d >= en) + "," + u + "," + (this._x1 = e + n * Math.cos(i)) + "," + (this._y1 = t + n * Math.sin(i))));
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
function sn(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-shape/src/point.js
function cn(e) {
	return e[0];
}
function ln(e) {
	return e[1];
}
//#endregion
//#region node_modules/d3-shape/src/array.js
var un = Array.prototype.slice;
//#endregion
//#region node_modules/d3-shape/src/link/index.js
function dn(e) {
	return e.source;
}
function fn(e) {
	return e.target;
}
function pn(e) {
	var t = dn, n = fn, r = cn, i = ln, a = null;
	function o() {
		var o, s = un.call(arguments), c = t.apply(this, s), l = n.apply(this, s);
		if (a ||= o = on(), e(a, +r.apply(this, (s[0] = c, s)), +i.apply(this, s), +r.apply(this, (s[0] = l, s)), +i.apply(this, s)), o) return a = null, o + "" || null;
	}
	return o.source = function(e) {
		return arguments.length ? (t = e, o) : t;
	}, o.target = function(e) {
		return arguments.length ? (n = e, o) : n;
	}, o.x = function(e) {
		return arguments.length ? (r = typeof e == "function" ? e : sn(+e), o) : r;
	}, o.y = function(e) {
		return arguments.length ? (i = typeof e == "function" ? e : sn(+e), o) : i;
	}, o.context = function(e) {
		return arguments.length ? (a = e ?? null, o) : a;
	}, o;
}
function mn(e, t, n, r, i) {
	e.moveTo(t, n), e.bezierCurveTo(t = (t + r) / 2, n, t, i, r, i);
}
function hn() {
	return pn(mn);
}
//#endregion
//#region node_modules/d3-sankey/src/sankeyLinkHorizontal.js
function gn(e) {
	return [e.source.x1, e.y0];
}
function _n(e) {
	return [e.target.x0, e.y1];
}
function vn() {
	return hn().source(gn).target(_n);
}
//#endregion
//#region src/board-sankey.ts
function yn(e = []) {
	let n = e.filter((e) => e.source && e.target && Number.isFinite(e.value) && e.value > 0);
	if (!n.length) return "";
	let r = [...new Set(n.map((e) => e.source))], i = [...new Set(n.map((e) => e.target))], a = $t().nodeId((e) => e.id).nodeWidth(10).nodePadding(22).extent([[155, 16], [535, 404]])({
		nodes: [...r.map((e) => ({
			id: `source:${e}`,
			name: e,
			side: "source"
		})), ...i.map((e) => ({
			id: `target:${e}`,
			name: e,
			side: "target"
		}))],
		links: n.map((e) => ({
			source: `source:${e.source}`,
			target: `target:${e.target}`,
			value: e.value
		}))
	}), o = n.reduce((e, t) => e + t.value, 0), s = vn(), c = a.links.map((e) => {
		let n = e.source, i = e.target;
		return `<path d="${s(e)}" stroke-width="${Math.max(.5, e.width || 0)}" style="--flow-color:var(--board-chart-${r.indexOf(n.name) % 6})" data-flow-source="${n.index}" data-flow-target="${i.index}" data-flow-value="${e.value}" data-flow-label="${t(n.name)} → ${t(i.name)}" tabindex="0" role="img" aria-label="${t(n.name)} → ${t(i.name)}：${e.value} 条线索"/>`;
	}).join(""), l = a.nodes.map((e) => `<g data-flow-node="${e.index}" data-flow-value="${e.value}" data-flow-label="${t(e.name)}" tabindex="0" role="img" aria-label="${t(e.name)}：${e.value} 条线索"><rect x="${e.x0}" y="${e.y0}" width="10" height="${Math.max(1, (e.y1 || 0) - (e.y0 || 0))}" rx="5" fill="${e.side === "source" ? `var(--board-chart-${r.indexOf(e.name) % 6})` : "var(--color-text-secondary)"}"/><text x="${e.side === "source" ? 145 : 545}" y="${((e.y0 || 0) + (e.y1 || 0)) / 2}" text-anchor="${e.side === "source" ? "end" : "start"}" dominant-baseline="middle">${t(e.name.length > 18 ? e.name.slice(0, 16) + "…" : e.name)}<tspan x="${e.side === "source" ? 145 : 545}" dy="15">${e.side === "source" ? e.value?.toLocaleString() : ((e.value || 0) / o * 100).toFixed(1) + "%"}</tspan></text></g>`).join("");
	return `<section class="board-sankey-card" data-sankey-card><header><h3>创作者线索来源</h3><b data-sankey-number>${o.toLocaleString()}</b><span data-sankey-label>条线索</span></header><div class="board-sankey-scroll"><svg viewBox="0 0 720 435" aria-label="来源网站与创作者线索"><g class="board-sankey-links">${c}</g><g class="board-sankey-nodes">${l}</g></svg></div><footer><span>来源网站</span><span>创作者 · 线索占比</span></footer></section>`;
}
function bn(e) {
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
var xn = (e) => Number.isFinite(e) && e >= 0;
function Sn(e, n, r = "个视频") {
	let i = e.filter((e) => xn(e.value));
	if (!i.length) return "";
	let a = i.reduce((e, t) => e + t.value, 0), o = Math.max(1, ...i.map((e) => e.value)) * 1.1, s = Math.min(22, 110 / Math.max(1, i.length)), c = Math.min(15, s * .68), l = i.map((e, n) => {
		let i = 32 + n * s, a = e.value / o * 100;
		return `<g style="--ring-color:var(--board-chart-${n % 6});--ring-delay:${n * 60}ms"><circle class="board-ring-track" cx="160" cy="160" r="${i}" stroke-width="${c}"/><circle class="board-ring-value" data-radial-ring="${n}" tabindex="0" role="button" aria-label="${t(e.name)}：${e.value.toLocaleString()} ${t(r)}" aria-pressed="false" cx="160" cy="160" r="${i}" stroke-width="${c}" pathLength="100" stroke-dasharray="${a} ${100 - a}" style="--ring-length:${a}" transform="rotate(-90 160 160)"/></g>`;
	}).join("");
	return `<section class="board-radial-card" data-radial-card data-radial-total="${a}" data-radial-title="${t(n)}"><header><span data-radial-label>${t(n)}</span><b data-radial-number>${a.toLocaleString()}</b><small>${t(r)}</small></header><svg class="board-rings" viewBox="0 0 320 320" aria-label="${t(n)}">${l}</svg><div class="board-radial-tiles">${i.map((e, n) => `<button type="button" data-radial-tile="${n}" data-radial-value="${e.value}" data-radial-name="${t(e.name)}" aria-pressed="false" style="--ring-color:var(--board-chart-${n % 6})"><span><i aria-hidden="true"></i>${t(e.name)}</span><b>${e.value.toLocaleString()}</b>${e.detail ? `<small>${t(e.detail)}</small>` : ""}</button>`).join("")}</div></section>`;
}
function Cn(e) {
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
var wn = [
	"周一",
	"周二",
	"周三",
	"周四",
	"周五",
	"周六",
	"周日"
];
function Tn(e) {
	if (!e?.days?.length) return "<section class=\"board-activity-empty\"><h3>浏览活跃时间</h3><p>还没有可用于分析的口味网站访问记录。</p></section>";
	let n = Array.from({ length: 7 }, () => Array(24).fill(0));
	for (let t of e.hours || []) Number.isInteger(t.weekday) && t.weekday >= 0 && t.weekday < 7 && Number.isInteger(t.hour) && t.hour >= 0 && t.hour < 24 && xn(t.count) && (n[t.weekday][t.hour] = (n[t.weekday][t.hour] || 0) + t.count);
	let r = Math.max(1, ...n.flat()), i = n.flat().reduce((e, t) => e + t, 0), a = n.map((e, t) => `<span class="board-heat-axis">${wn[t]}</span>${e.map((e, n) => `<button type="button" data-heat-value="${e}" data-heat-label="${wn[t]} ${n}:00" aria-label="${wn[t]} ${n}:00，${e} 次访问" style="--heat:${e ? Math.max(12, e / r * 100) : 0}%"></button>`).join("")}`).join(""), o = e.days.filter((e) => /^\d{4}-\d{2}-\d{2}$/.test(e.date) && xn(e.count)).sort((e, t) => e.date.localeCompare(t.date));
	if (!o.length) return "";
	let s = /* @__PURE__ */ new Date(`${o.at(-1).date}T00:00:00Z`), c = new Date(s);
	c.setUTCDate(c.getUTCDate() - 90);
	let l = new Map(o.map((e) => [e.date, e.count])), u = Math.max(1, ...o.map((e) => e.count)), d = Array.from({ length: 91 }, (e, t) => {
		let n = new Date(c);
		n.setUTCDate(c.getUTCDate() + t);
		let r = n.toISOString().slice(0, 10), i = l.get(r) || 0;
		return `<button type="button" data-heat-value="${i}" data-heat-label="${r}" aria-label="${r}，${i} 次访问" style="--heat:${i ? Math.max(12, i / u * 100) : 0}%"></button>`;
	}).join("");
	return `<div class="board-activity-charts"><section class="board-heat-card" data-heat-card><header><h3>浏览活跃时间</h3><b data-heat-number>${i.toLocaleString()}</b><span data-heat-title data-heat-default="口味网站访问">口味网站访问</span></header><div class="board-heat-scroll"><div class="board-hour-grid"><span></span>${Array.from({ length: 24 }, (e, t) => `<span class="board-heat-axis">${t % 2 ? "" : t}</span>`).join("")}${a}</div></div><footer>星期 × 小时<span>${t(e.timezone || "UTC+08:00")}</span></footer></section><section class="board-heat-card" data-heat-card><header><h3>每日活跃</h3><b data-heat-number>${o.filter((e) => e.date >= c.toISOString().slice(0, 10)).reduce((e, t) => e + t.count, 0).toLocaleString()}</b><span data-heat-title data-heat-default="口味网站访问">口味网站访问</span></header><div class="board-day-grid">${d}</div><footer>${c.toISOString().slice(0, 10)}<span>${o.at(-1).date}</span></footer></section></div>`;
}
function En(e) {
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
var Dn = (e) => e.replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function On(e, t, n = "", r = "") {
	if (!t) return "";
	let i = `sidebar-group-${encodeURIComponent(e)}`;
	return `<details class="sec${r ? " cat-" + Dn(r) : ""}" data-sidebar-group="${Dn(e)}"><summary role="button" class="board-section-toggle"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${Dn(e)}</span></summary><div class="board-sidebar-body" id="${i}">${t}${n}</div></details>`;
}
function kn(e) {
	e.querySelectorAll("[data-sidebar-group]").forEach((e) => {
		if (e.dataset.sidebarWired) return;
		e.dataset.sidebarWired = "true";
		let t = e.querySelector(".board-sidebar-body"), n = `peach.sidebar.group.${e.dataset.sidebarGroup}`, r = null;
		try {
			r = sessionStorage.getItem(n);
		} catch {}
		let i = !!t.querySelector("[aria-pressed=true]");
		e.open = r === null ? i : r === "open";
	}), S(e, "details[data-sidebar-group]", "sidebar-collapse"), e.querySelectorAll(".board-section-toggle").forEach((e) => {
		e.dataset.persistWired || (e.dataset.persistWired = "true", e.addEventListener("click", () => {
			let t = `peach.sidebar.group.${e.closest("[data-sidebar-group]").dataset.sidebarGroup}`;
			try {
				sessionStorage.setItem(t, e.getAttribute("aria-expanded") === "true" ? "open" : "closed");
			} catch {}
		}));
	});
}
var An = !1;
async function jn(e, t) {
	if (An) return;
	if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
		t();
		return;
	}
	let n = e.getBoundingClientRect(), r = n.left + n.width / 2, i = n.top + n.height / 2, a = Math.hypot(Math.max(r, innerWidth - r), Math.max(i, innerHeight - i)) * 2.5, o = document.createElement("style");
	o.textContent = `::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:radial-gradient(circle closest-side,#000 78%,#0006 88%,transparent);mask-repeat:no-repeat;will-change:mask-position,mask-size;animation:peach-theme-reveal 560ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${r}px ${i}px;mask-size:0px 0px}to{mask-position:${r - a / 2}px ${i - a / 2}px;mask-size:${a}px ${a}px}}`, An = !0, document.head.append(o);
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
		delete s.dataset.themeSnapshot, o.remove(), An = !1;
	}
}
//#endregion
//#region src/settings-controls.tsx
function Mn({ value: e, options: t, label: n, onChange: r, disabled: i = !1, className: a = "", fixed: o = !1 }) {
	let s = H(null), c = H(null), l = H(r);
	l.current = r;
	let u = JSON.stringify(t);
	return V(() => {
		let r = s.current;
		r.innerHTML = y(t, e, {
			label: n,
			className: "configselect",
			attr: o ? "data-fixed-width" : ""
		});
		let i = C(r.firstElementChild);
		c.current = i;
		let a = () => l.current(i.value);
		return i.addEventListener("change", a), () => {
			i.disabled = !0, i.removeEventListener("change", a), c.current = null, r.replaceChildren();
		};
	}, [
		u,
		n,
		o
	]), V(() => {
		c.current && (c.current.value = e, c.current.disabled = i);
	}, [
		e,
		i,
		u,
		n,
		o
	]), /* @__PURE__ */ K("div", {
		ref: s,
		class: a
	});
}
function Nn(e, t = "") {
	let n = H(!1), r = H(new AbortController()), [i, a] = z(t);
	B(() => () => r.current.abort(), []);
	async function o(t, i, o) {
		if (!(n.current || r.current.signal.aborted)) {
			n.current = !0, a(""), x(e.current, !0);
			try {
				let e = await t(r.current.signal);
				r.current.signal.aborted || i(e);
			} catch (e) {
				r.current.signal.aborted || (o ? o(e) : a(U(e)));
			} finally {
				n.current = !1, r.current.signal.aborted || x(e.current, !1);
			}
		}
	}
	return {
		run: o,
		error: i,
		setError: a,
		busy: n
	};
}
function Pn({ id: e, titleId: t, title: n, help: r, error: i, children: a, footer: o, onSubmit: s, formRef: c, noValidate: l, warning: u }) {
	return /* @__PURE__ */ K("form", {
		id: e,
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"data-fieldset-type": u ? "warning" : void 0,
		"aria-labelledby": t,
		onSubmit: s,
		ref: c ?? null,
		noValidate: l,
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: p(t, n) } }), r && /* @__PURE__ */ K("p", {
						class: "confighelp",
						children: r
					})]
				}),
				a,
				i && /* @__PURE__ */ K("p", {
					class: "configbad",
					role: "alert",
					children: i
				})
			]
		}), o && /* @__PURE__ */ K("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: o
		})]
	});
}
//#endregion
//#region src/islands/access-settings.tsx
function Fn({ id: e, label: t, value: n, onInput: r, error: i, help: a, current: o = !1, disabled: s = !1 }) {
	return /* @__PURE__ */ K("div", {
		class: "configfield",
		children: [
			/* @__PURE__ */ K("label", {
				for: e,
				children: t
			}),
			/* @__PURE__ */ K("input", {
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
			i || a ? /* @__PURE__ */ K("p", {
				id: `${e}-hint`,
				class: i ? "configbad" : "confighelp",
				role: i ? "alert" : void 0,
				children: i || a
			}) : null
		]
	});
}
function In({ initial: e, receipt: t }) {
	let [n, r] = z(e), [i, a] = z(""), [o, s] = z(""), [c, l] = z(""), [u, d] = z(!1), [f, p] = z({}), m = H(null), h = H(null), { run: _, error: v, setError: y, busy: b } = Nn(h);
	return /* @__PURE__ */ K(Pn, {
		titleId: "accessTitle",
		title: "访问密码",
		warning: u,
		onSubmit: async (e) => {
			if (e.preventDefault(), b.current) return;
			y("");
			let f = {};
			if (n.mode === "password" && !i && (f.current_password = "请输入当前访问密码"), u || ((o.length < 8 || o.length > 256) && (f.password = "访问密码需为 8–256 个字符"), o !== c && (f.confirmation = "两次输入的密码不一致")), p(f), Object.keys(f).length) {
				requestAnimationFrame(() => m.current?.querySelector("[aria-invalid=\"true\"]")?.focus());
				return;
			}
			await _((e) => G("/api/configuration/access", {
				revision: n.revision,
				action: u ? "disable" : "set",
				confirm_disable: u,
				current_password: i,
				password: u ? "" : o,
				confirmation: u ? "" : c
			}, "POST", e), (e) => {
				r(e), a(""), s(""), l(""), d(!1), p({}), t(e.mode === "open" ? "已关闭访问密码" : "已保存访问密码");
			}, (e) => {
				let t = e instanceof dt ? e.body : null, n = t?.errors || t?.detail?.errors;
				n ? p(n) : y(U(e));
			});
		},
		noValidate: !0,
		formRef: m,
		error: v,
		help: n.mode === "legacy" ? "当前使用系统生成的访问口令。你可以设置自己的密码，或关闭登录要求。" : n.mode === "locked" ? "访问设置无法读取，请在本机检查配置文件。" : n.mode === "password" ? "已设置密码。新设备需要登录，保持登录时间在登录页选择。" : void 0,
		footer: n.mode !== "locked" && /* @__PURE__ */ K(F, { children: [/* @__PURE__ */ K("p", { children: "保存后立即生效。" }), /* @__PURE__ */ K("button", {
			class: "geist-button primary",
			type: "submit",
			ref: h,
			children: "保存配置"
		})] }),
		children: [
			n.mode === "open" ? /* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: g("能连接到 Peach 的设备打开地址就能看馆藏，不需要登录。", {
				variant: "warning",
				label: "未设置访问密码"
			}) } }) : null,
			n.mode === "password" || n.mode === "legacy" ? /* @__PURE__ */ K("label", {
				class: "configcheck",
				children: [/* @__PURE__ */ K("span", {
					class: "pcheck",
					children: [/* @__PURE__ */ K("input", {
						type: "checkbox",
						checked: u,
						onChange: (e) => d(e.currentTarget.checked)
					}), /* @__PURE__ */ K("span", {
						"aria-hidden": "true",
						children: /* @__PURE__ */ K("svg", {
							viewBox: "0 0 24 24",
							children: /* @__PURE__ */ K("use", { href: "#i-check" })
						})
					})]
				}), /* @__PURE__ */ K("span", { children: "关闭访问密码，允许能连接到 Peach 的设备直接访问" })]
			}) : null,
			n.mode === "password" ? /* @__PURE__ */ K(Fn, {
				id: "access-current",
				label: "当前访问密码",
				value: i,
				onInput: a,
				error: f.current_password,
				current: !0
			}) : null,
			n.mode === "locked" ? null : /* @__PURE__ */ K(F, { children: [/* @__PURE__ */ K(Fn, {
				id: "access-password",
				label: n.mode === "password" ? "新访问密码" : "设置访问密码",
				value: o,
				onInput: s,
				disabled: u,
				error: u ? void 0 : f.password,
				help: u ? "关闭访问密码时无需填写。" : "至少 8 个字符。保存后其他设备需要重新登录。"
			}), /* @__PURE__ */ K(Fn, {
				id: "access-confirm",
				label: "确认访问密码",
				value: c,
				onInput: l,
				disabled: u,
				error: u ? void 0 : f.confirmation
			})] }),
			u && /* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: g("保存后，能连接到 Peach 的设备将直接访问馆藏。", {
				variant: "warning",
				label: "访问范围"
			}) } })
		]
	});
}
//#endregion
//#region src/islands/release-updates.tsx
var Ln = /* @__PURE__ */ new Set([
	"downloading",
	"verifying",
	"extracting",
	"preparing",
	"restarting",
	"installing"
]);
function Rn({ initial: e, initialJob: t }) {
	let [n, r] = z(e), [i, a] = z(t || {
		state: "idle",
		progress: 0
	}), [o, s] = z(""), c = H(null), l = H(!0), u = H(!1), f = H(null);
	B(() => {
		x(f.current, Ln.has(i.state));
	}, [i.state]), B(() => () => {
		l.current = !1, c.current?.abort();
	}, []);
	let m = async () => {
		let e = await G("/api/configuration/update-restart", {});
		l.current && a(e);
	};
	B(() => {
		i.state !== "ready" || u.current || (u.current = !0, d({
			title: "更新已准备好",
			body: `Peach ${i.version || ""} 将在重启后安装。`,
			confirmLabel: "立即重启",
			cancelLabel: "稍后",
			onConfirm: m
		}));
	}, [i.state]), B(() => {
		let e = new AbortController(), t, n = 0, o = async () => {
			try {
				let t = await W("/api/configuration/update-status", e.signal);
				if (!e.signal.aborted) {
					a(t), n = 0, t.state === "complete" && r((e) => ({
						...e,
						current_version: t.version || e.current_version,
						state: "current",
						message: "已是最新测试版。"
					}));
					let i = await W("/api/configuration/automatic-updates", e.signal);
					!e.signal.aborted && i.result && r(i.result);
				}
			} catch {
				++n >= 120 && !e.signal.aborted && s("尚未连接到 Peach，请检查托盘后刷新页面。");
			}
			!e.signal.aborted && n < 120 && (t = setTimeout(o, Ln.has(i.state) ? 1e3 : 3e4));
		};
		return t = setTimeout(o, Ln.has(i.state) ? 1e3 : 3e4), () => {
			e.abort(), clearTimeout(t);
		};
	}, [i.state]);
	let h = async (e) => {
		if (c.current || Ln.has(i.state)) return;
		let t = new AbortController();
		c.current = t, u.current = !1, s(""), x(e, !0);
		try {
			let e = await G("/api/configuration/update", {}, "POST", t.signal);
			t.signal.aborted || a(e);
		} catch (e) {
			t.signal.aborted || s(U(e));
		} finally {
			c.current = null, x(e, !1);
		}
	}, v = async (t) => {
		if (c.current) return;
		let n = new AbortController();
		c.current = n, x(t, !0), s("");
		try {
			let e = await W("/api/configuration/updates", n.signal);
			n.signal.aborted || r(e);
		} catch (t) {
			n.signal.aborted || (r({
				...e,
				state: "error"
			}), s(U(t)));
		} finally {
			c.current = null, x(t, !1);
		}
	};
	return /* @__PURE__ */ K("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configUpdatesTitle",
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: p("configUpdatesTitle", "检查更新") } }),
				/* @__PURE__ */ K("dl", {
					class: "configfacts",
					children: [
						/* @__PURE__ */ K("dt", { children: "当前版本" }),
						/* @__PURE__ */ K("dd", { children: n.current_version }),
						/* @__PURE__ */ K("dt", { children: "安装方式" }),
						/* @__PURE__ */ K("dd", { children: n.installation }),
						/* @__PURE__ */ K("dt", { children: "更新通道" }),
						/* @__PURE__ */ K("dd", { children: n.channel }),
						/* @__PURE__ */ K("dt", { children: "最新版本" }),
						/* @__PURE__ */ K("dd", { children: n.latest_version || (n.state === "unchecked" ? "尚未检查" : "未取得") })
					]
				}),
				n.checked_at ? /* @__PURE__ */ K("p", {
					class: "confighelp",
					children: ["检查于 ", (/* @__PURE__ */ new Date(n.checked_at * 1e3)).toLocaleString()]
				}) : null,
				n.state === "available" && !o ? /* @__PURE__ */ K("div", {
					role: "status",
					dangerouslySetInnerHTML: { __html: g(n.message, { label: "有可用更新" }) }
				}) : /* @__PURE__ */ K("p", {
					class: o || n.state === "error" ? "configbad" : "confighelp",
					role: o || n.state === "error" ? "alert" : "status",
					children: o || n.message
				}),
				i.state === "idle" ? null : /* @__PURE__ */ K("div", {
					"aria-live": "polite",
					children: [/* @__PURE__ */ K("p", {
						class: i.state === "error" ? "configbad" : "confighelp",
						children: i.message
					}), i.state === "error" ? null : /* @__PURE__ */ K(F, { children: [
						/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: _("更新准备进度：下载、校验、解压、准备安装", i.progress, 100, { stops: [
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
						/* @__PURE__ */ K("p", {
							class: "confighelp",
							children: ["下载 → 校验 → 解压 → 准备安装 · ", i.message]
						}),
						/* @__PURE__ */ K("p", {
							class: "confighelp",
							children: i.state === "downloading" && i.total ? `${((i.downloaded || 0) / 1048576).toFixed(1)} / ${(i.total / 1048576).toFixed(1)} MB` : `${i.progress}%`
						})
					] })]
				})
			]
		}), /* @__PURE__ */ K("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [
				/* @__PURE__ */ K("a", {
					class: "externallink",
					href: n.release_url,
					target: "_blank",
					rel: "noreferrer",
					children: ["查看发布页", /* @__PURE__ */ K("svg", {
						class: "externalmark",
						viewBox: "0 0 24 24",
						"aria-hidden": "true",
						children: /* @__PURE__ */ K("use", { href: "#i-external-link" })
					})]
				}),
				i.state === "ready" ? /* @__PURE__ */ K("button", {
					type: "button",
					class: "geist-button primary",
					onClick: () => {
						d({
							title: "更新已准备好",
							body: `Peach ${i.version || ""} 将在重启后安装。`,
							confirmLabel: "立即重启",
							cancelLabel: "稍后",
							onConfirm: m
						});
					},
					children: "重启安装"
				}) : null,
				n.state === "available" && n.installation === "独立测试包" && i.state !== "ready" ? /* @__PURE__ */ K("button", {
					ref: f,
					type: "button",
					class: "geist-button primary",
					onClick: (e) => h(e.currentTarget),
					children: "下载并安装"
				}) : null,
				/* @__PURE__ */ K("button", {
					type: "button",
					class: "geist-button",
					disabled: Ln.has(i.state),
					onClick: (e) => v(e.currentTarget),
					children: "检查更新"
				})
			]
		})]
	});
}
//#endregion
//#region src/islands/automatic-updates.tsx
function zn({ initial: e, receipt: t }) {
	let [n, r] = z(e.mode), [i, a] = z(e.interval_hours), o = H(null), s = Nn(o, e.error), c = () => s.run((e) => G("/api/configuration/automatic-updates", {
		mode: n,
		interval_hours: i
	}, "POST", e), () => t("已保存自动更新设置"));
	return /* @__PURE__ */ K(Pn, {
		titleId: "automaticUpdatesTitle",
		title: "自动更新",
		error: s.error,
		onSubmit: (t) => {
			t.preventDefault(), e.available && c();
		},
		footer: /* @__PURE__ */ K("button", {
			ref: o,
			type: "submit",
			class: "geist-button",
			disabled: !e.available,
			children: "保存自动更新"
		}),
		children: [
			/* @__PURE__ */ K("div", {
				class: "configoptions",
				role: "group",
				"aria-labelledby": "automaticUpdatesTitle",
				children: [/* @__PURE__ */ K("label", {
					class: "configtoggle",
					children: [/* @__PURE__ */ K("span", { children: "自动检查新版本" }), /* @__PURE__ */ K("input", {
						class: "ptoggle",
						type: "checkbox",
						role: "switch",
						checked: n !== "off",
						disabled: !e.available,
						onChange: (e) => r(e.currentTarget.checked ? "check" : "off")
					})]
				}), /* @__PURE__ */ K("label", {
					class: "configtoggle",
					children: [/* @__PURE__ */ K("span", { children: "自动下载更新" }), /* @__PURE__ */ K("input", {
						class: "ptoggle",
						type: "checkbox",
						role: "switch",
						checked: n === "download",
						disabled: !e.available || !e.download_available || n === "off",
						onChange: (e) => r(e.currentTarget.checked ? "download" : "check")
					})]
				})]
			}),
			/* @__PURE__ */ K(Mn, {
				value: String(i),
				onChange: (e) => a(Number(e)),
				label: "检查频率",
				fixed: !0,
				options: [
					["6", "每 6 小时"],
					["24", "每天"],
					["168", "每周"]
				]
			}),
			/* @__PURE__ */ K("p", {
				class: "confighelp",
				children: e.available ? e.download_available ? "开启后一分钟内开始检查。下载完成后，在此确认重启安装。" : "开启后一分钟内开始检查。源码运行请前往发布页获取新版本。" : "自动更新需要由托盘管理的服务。"
			})
		]
	});
}
//#endregion
//#region src/islands/peach-proxy.tsx
function Bn({ initial: e, receipt: t }) {
	let [n, r] = z(e), [i, a] = z(e.mode), [o, s] = z(""), c = H(null), l = Nn(c), u = () => l.run((e) => G("/api/configuration/peach-proxy", {
		mode: i,
		proxy: o
	}, "POST", e), (e) => {
		r(e), s(""), t("已保存 Peach 代理");
	});
	return /* @__PURE__ */ K(Pn, {
		id: "peachProxy",
		titleId: "peachProxyTitle",
		title: "Peach 代理",
		help: "采集来源选择“Peach 代理”时共用此设置。",
		error: l.error,
		onSubmit: (e) => {
			e.preventDefault(), u();
		},
		footer: /* @__PURE__ */ K("button", {
			ref: c,
			class: "geist-button primary",
			type: "submit",
			children: "保存代理"
		}),
		children: [
			/* @__PURE__ */ K(Mn, {
				value: i,
				onChange: a,
				label: "Peach 代理",
				fixed: !0,
				options: [
					["environment", "系统代理"],
					["direct", "直连"],
					["proxy", "自定义"]
				]
			}),
			i === "proxy" && /* @__PURE__ */ K("div", {
				class: "configfield",
				children: [/* @__PURE__ */ K("label", {
					htmlFor: "peachProxyAddress",
					children: "代理地址"
				}), /* @__PURE__ */ K("input", {
					id: "peachProxyAddress",
					class: "geist-input",
					type: "password",
					autoComplete: "off",
					value: o,
					placeholder: n.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
					onInput: (e) => s(e.currentTarget.value)
				})]
			}),
			n.needs_selection && /* @__PURE__ */ K("p", {
				class: "configbad",
				children: "已有来源的代理地址不同，请选择公共连接方式。"
			})
		]
	});
}
//#endregion
//#region src/islands/desktop-settings.tsx
function Vn({ label: e, checked: t, disabled: n, change: r }) {
	return /* @__PURE__ */ K("label", {
		class: "configcheck",
		children: [/* @__PURE__ */ K("span", {
			class: "pcheck",
			children: [/* @__PURE__ */ K("input", {
				type: "checkbox",
				checked: t,
				disabled: n,
				onChange: (e) => r(e.currentTarget.checked)
			}), /* @__PURE__ */ K("span", {
				"aria-hidden": "true",
				children: /* @__PURE__ */ K("svg", {
					viewBox: "0 0 24 24",
					children: /* @__PURE__ */ K("use", { href: "#i-check" })
				})
			})]
		}), /* @__PURE__ */ K("span", { children: e })]
	});
}
function Hn({ label: e, checked: t, disabled: n, change: r }) {
	return /* @__PURE__ */ K("label", {
		class: "configtoggle",
		children: [/* @__PURE__ */ K("span", { children: e }), /* @__PURE__ */ K("input", {
			class: "ptoggle",
			type: "checkbox",
			role: "switch",
			checked: t,
			disabled: n,
			onChange: (e) => r(e.currentTarget.checked)
		})]
	});
}
function Un({ startup: e, receipt: t }) {
	let [n, r] = z(e.enabled), [i, a] = z(e.silent), [o, s] = z(e.desktop), [c, l] = z(""), u = H(!1), d = H(null), f = e.available && !e.desktop_message;
	async function m() {
		if (!u.current) {
			u.current = !0, x(d.current, !0), l("");
			try {
				await G("/api/configuration/startup", {
					enabled: n,
					silent: i,
					desktop: o
				}), t("已保存开机自启");
			} catch (e) {
				l(U(e));
			} finally {
				u.current = !1, x(d.current, !1);
			}
		}
	}
	return /* @__PURE__ */ K("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), m();
		},
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: p("startupTitle", "开机自启") } }),
				/* @__PURE__ */ K("div", {
					class: "configoptions",
					role: "group",
					"aria-labelledby": "startupTitle",
					children: [
						/* @__PURE__ */ K(Hn, {
							label: "开机后启动 Peach",
							checked: n,
							disabled: !e.available,
							change: r
						}),
						/* @__PURE__ */ K("div", {
							class: "configoption",
							children: [/* @__PURE__ */ K(Hn, {
								label: "静默启动",
								checked: i,
								disabled: !e.available || !n,
								change: a
							}), /* @__PURE__ */ K("p", {
								class: "confighelp",
								children: "静默启动仅显示托盘，开机后启动 Peach 打开时生效。"
							})]
						}),
						/* @__PURE__ */ K("div", {
							class: "configoption",
							children: [/* @__PURE__ */ K(Hn, {
								label: "在桌面创建快捷方式",
								checked: o,
								disabled: !f,
								change: s
							}), /* @__PURE__ */ K("p", {
								class: "confighelp",
								children: e.desktop_message || "双击图标打开 Peach 网页；卸载时一并移除。"
							})]
						})
					]
				}),
				e.message && /* @__PURE__ */ K("p", {
					class: "confighelp",
					children: e.message
				}),
				c && /* @__PURE__ */ K("p", {
					class: "configbad",
					role: "alert",
					children: c
				})
			]
		}), /* @__PURE__ */ K("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ K("button", {
				ref: d,
				type: "submit",
				class: "geist-button primary",
				disabled: !e.available,
				children: "保存配置"
			})
		})]
	});
}
function Wn({ data: e }) {
	let t = H(null);
	return V(() => {
		let n = t.current, r = document.createElement("details");
		r.className = "configdirectories";
		let a = document.createElement("summary");
		a.innerHTML = i("chevron-right") + "<span>数据目录</span>", r.append(a);
		for (let t of [.../* @__PURE__ */ new Set([e.data_root, ...e.directories])]) {
			let e = document.createElement("p");
			e.className = "confighelp", e.textContent = t, r.append(e);
		}
		return n.replaceChildren(r), S(n, "details", "uninstall-data"), () => n.replaceChildren();
	}, [e]), /* @__PURE__ */ K("div", { ref: t });
}
function Gn({ uninstall: e }) {
	let [t, n] = z(!1), [r, i] = z("");
	async function a() {
		await d({
			title: "卸载 Peach",
			danger: !0,
			body: t ? "将退出 Peach，移除程序、开机自启、桌面图标、设置、本地数据库、观看记录、凭据和缓存。原始媒体文件保留。" : "将退出 Peach 并移除程序、开机自启和桌面图标。设置、本地数据库、观看记录与缓存保留。",
			confirmLabel: "卸载 Peach",
			onConfirm: async () => {
				let e = await G("/api/configuration/uninstall", {
					delete_data: t,
					confirmation: "卸载 Peach"
				});
				i(e.message);
			}
		});
	}
	let o = r || e.message;
	return /* @__PURE__ */ K("section", {
		id: "uninstallPeach",
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"data-fieldset-type": "error",
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: p("uninstallTitle", "卸载 Peach") } }), e.available && /* @__PURE__ */ K("p", {
						class: "confighelp",
						children: "卸载会退出 Peach、移除程序、开机自启和桌面图标。原始媒体文件保留。"
					})]
				}),
				/* @__PURE__ */ K(Vn, {
					label: "完全卸载：同时删除设置、本地数据库、观看记录、凭据和缓存",
					checked: t,
					disabled: !e.full_available || !!r,
					change: n
				}),
				/* @__PURE__ */ K(Wn, { data: e })
			]
		}), /* @__PURE__ */ K("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [o && /* @__PURE__ */ K("p", {
				role: r ? "status" : void 0,
				children: o
			}), /* @__PURE__ */ K("button", {
				type: "button",
				class: "geist-button danger",
				disabled: !e.available || !!r,
				onClick: () => void a(),
				children: "卸载 Peach"
			})]
		})]
	});
}
//#endregion
//#region src/islands/clouddrive-guide.tsx
var Kn = [
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
function qn() {
	let e = H(null);
	return V(() => {
		e.current && S(e.current, "details", "clouddrive-guide");
	}, []), /* @__PURE__ */ K("div", {
		ref: e,
		class: "cloudguide",
		children: [/* @__PURE__ */ K("p", {
			class: "confighelp",
			children: ["先在 CloudDrive 登录网盘并挂载，开启「启动时自动挂载」。", /* @__PURE__ */ K("a", {
				class: "externallink",
				href: "https://www.clouddrive2.com/help.html",
				target: "_blank",
				rel: "noreferrer",
				children: ["挂载帮助", /* @__PURE__ */ K("svg", {
					class: "externalmark",
					viewBox: "0 0 24 24",
					"aria-hidden": "true",
					children: /* @__PURE__ */ K("use", { href: "#i-external-link" })
				})]
			})]
		}), /* @__PURE__ */ K("details", { children: [
			/* @__PURE__ */ K("summary", { children: [/* @__PURE__ */ K("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true",
				children: /* @__PURE__ */ K("use", { href: "#i-chevron-right" })
			}), "CloudDrive 缓存建议"] }),
			/* @__PURE__ */ K("p", {
				class: "confighelp",
				children: "看缓存放在哪块硬盘上，照那一行填。这是起步值，填得越大不一定越快。"
			}),
			/* @__PURE__ */ K("div", {
				class: "cloudguide-tablewrap",
				children: /* @__PURE__ */ K("table", {
					class: "cloudguide-table",
					children: [/* @__PURE__ */ K("thead", { children: /* @__PURE__ */ K("tr", { children: [
						/* @__PURE__ */ K("th", {
							scope: "col",
							children: "缓存所在硬盘"
						}),
						/* @__PURE__ */ K("th", {
							scope: "col",
							children: "缓存上限"
						}),
						/* @__PURE__ */ K("th", {
							scope: "col",
							children: "读取长度（默认 / 最小）"
						}),
						/* @__PURE__ */ K("th", {
							scope: "col",
							children: "同时处理视频"
						})
					] }) }), /* @__PURE__ */ K("tbody", { children: Kn.map((e) => /* @__PURE__ */ K("tr", { children: [
						/* @__PURE__ */ K("th", {
							scope: "row",
							children: e.name
						}),
						/* @__PURE__ */ K("td", {
							"data-label": "缓存上限",
							children: e.cache
						}),
						/* @__PURE__ */ K("td", {
							"data-label": "读取长度（默认 / 最小）",
							children: e.read
						}),
						/* @__PURE__ */ K("td", {
							"data-label": "同时处理视频",
							children: e.task
						})
					] }, e.name)) })]
				})
			}),
			/* @__PURE__ */ K("ul", {
				class: "cloudguide-notes",
				children: [
					/* @__PURE__ */ K("li", { children: "缓存上限和清理方式填在 CloudDrive「设置」里，清理方式选 LRU。上限不要填 0，系统盘至少留 40 GiB；填完重开设置页确认存住了。" }),
					/* @__PURE__ */ K("li", { children: "读取长度和下载线程填在每个网盘各自的下载设置里，线程都从 2 开始。" }),
					/* @__PURE__ */ K("li", { children: "Buffer Cache 占内存，磁盘缓存和文件夹缓存占硬盘，改一个管不住另外两个。" })
				]
			}),
			/* @__PURE__ */ K("p", {
				class: "confighelp",
				children: [
					"三处缓存分别管什么、这几个值怎么往上调、码率和速度怎么换算、线程上限与直链代理怎么取舍，以及这些起步值的来源，都在",
					/* @__PURE__ */ K("a", {
						class: "externallink",
						href: "https://github.com/longmeidao/peach/blob/master/docs/CLOUDDRIVE.md",
						target: "_blank",
						rel: "noreferrer",
						children: ["CloudDrive 配置与调优", /* @__PURE__ */ K("svg", {
							class: "externalmark",
							viewBox: "0 0 24 24",
							"aria-hidden": "true",
							children: /* @__PURE__ */ K("use", { href: "#i-external-link" })
						})]
					}),
					"。"
				]
			})
		] })]
	});
}
//#endregion
//#region src/library-icon-picker.tsx
var Jn = [
	["", "自动识别"],
	["hard-drive", "磁盘"],
	["database", "资料库"],
	["heart", "心动"],
	["heart-hand", "亲密"],
	["flame", "热情"],
	["cherry", "樱桃"],
	["lollipop", "甜心"],
	["candy", "糖果"],
	["banana", "香蕉"],
	["droplets", "湿润"],
	["venus", "女性"],
	["mars", "男性"],
	["venus-and-mars", "情侣"],
	["gem", "精选"],
	["crown", "女王"],
	["ribbon", "丝带"],
	["shirt", "制服"],
	["graduation-cap", "学生"],
	["stethoscope", "护士"],
	["glasses", "眼镜"],
	["footprints", "足迹"],
	["hand", "手部"],
	["flower", "花朵"],
	["venetian-mask", "角色扮演"],
	["rabbit", "兔女郎"],
	["paw-print", "兽耳"],
	["dumbbell", "健身"],
	["bed-double", "卧室"],
	["bath", "浴室"],
	["key-round", "私密"],
	["wine", "微醺"],
	["cigarette", "烟"],
	["moon", "夜色"],
	["sparkles", "幻想"],
	["camera", "写真"],
	["video", "影片"],
	["film", "电影"],
	["image", "图集"],
	["gamepad-2", "游戏"],
	["star", "收藏"],
	["tags", "主题"]
];
function Yn(e) {
	let t = e === "local" ? "" : s[e];
	return t ? [t, "自动识别"] : ["hard-drive", "默认"];
}
function Xn({ value: e, label: t, kind: n = "local", onChange: r }) {
	let [i, a] = z(e), o = H(null), s = H(null), [c, l] = Yn(n), u = (e) => /* @__PURE__ */ K("span", {
		"aria-hidden": "true",
		dangerouslySetInnerHTML: { __html: b(e || c) }
	}), d = (e, t) => e ? t : l;
	return /* @__PURE__ */ K("div", {
		class: "board-icon-picker",
		children: [/* @__PURE__ */ K("button", {
			ref: s,
			type: "button",
			class: "geist-button board-icon-trigger",
			"aria-label": t,
			"aria-haspopup": "dialog",
			onClick: () => {
				a(e);
				let t = o.current, n = s.current.getBoundingClientRect();
				t.showModal();
				let r = t.getBoundingClientRect();
				t.style.left = `${Math.max(8, Math.min(innerWidth - r.width - 8, n.left))}px`, t.style.top = `${n.bottom + r.height + 8 <= innerHeight ? n.bottom + 4 : Math.max(8, n.top - r.height - 4)}px`;
			},
			children: [u(e), /* @__PURE__ */ K("span", { children: d(e, Jn.find(([t]) => t === e)?.[1] || l) })]
		}), /* @__PURE__ */ K("dialog", {
			ref: o,
			class: "board-icon-popover",
			"aria-label": `${t}候选`,
			onCancel: () => a(e),
			onClick: (t) => {
				t.target === o.current && (o.current?.close(), a(e));
			},
			children: [/* @__PURE__ */ K("div", {
				class: "board-icon-panel",
				children: [/* @__PURE__ */ K("h3", { children: "选择媒体库图标" }), /* @__PURE__ */ K("div", {
					role: "radiogroup",
					"aria-label": "候选图标",
					class: "board-icon-grid",
					children: Jn.map(([e, n]) => /* @__PURE__ */ K("label", {
						title: d(e, n),
						class: i === e ? "selected" : "",
						children: [/* @__PURE__ */ K("input", {
							type: "radio",
							name: `${t}-icon`,
							"aria-label": d(e, n),
							value: e,
							checked: i === e,
							onChange: () => a(e)
						}), u(e)]
					}))
				})]
			}), /* @__PURE__ */ K("footer", { children: [/* @__PURE__ */ K("button", {
				type: "button",
				class: "geist-button",
				onClick: () => {
					a(e), o.current.close();
				},
				children: "取消"
			}), /* @__PURE__ */ K("button", {
				type: "button",
				class: "geist-button primary",
				disabled: i === e,
				onClick: () => {
					r(i), o.current.close();
				},
				children: "应用"
			})] })]
		})]
	});
}
//#endregion
//#region src/islands/configuration.tsx
var Zn = "/api/configuration", Qn = "/api/pick-folder", $n = 8e3, er = (e, t) => W(Zn, t), tr = ({ html: e, class: t }) => /* @__PURE__ */ K("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), nr = (e) => !(e instanceof dt) || e.status !== 400 ? null : e.body?.errors ?? null;
function rr({ facts: e }) {
	return /* @__PURE__ */ K("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ K(tr, { html: p("configFactsTitle", "运行信息") }), /* @__PURE__ */ K("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ K(F, { children: [/* @__PURE__ */ K("dt", { children: e.term }), /* @__PURE__ */ K("dd", { children: [e.value, e.download_url ? /* @__PURE__ */ K("span", {
					class: "confighelp",
					children: [" ", /* @__PURE__ */ K("a", {
						class: "externallink",
						href: e.download_url,
						target: "_blank",
						rel: "noreferrer",
						children: [e.download_label, /* @__PURE__ */ K("svg", {
							class: "externalmark",
							viewBox: "0 0 24 24",
							"aria-hidden": "true",
							children: /* @__PURE__ */ K("use", { href: "#i-external-link" })
						})]
					})]
				}) : null] })] }))
			})]
		})
	});
}
function ir({ data: e }) {
	let [t, n] = z(e.media_sources), [r, i] = z(""), a = H(null);
	B(() => () => a.current?.abort(), []);
	let o = async (e) => {
		if (a.current) return;
		let t = new AbortController();
		a.current = t, x(e, !0), i("");
		try {
			let e = await W(Zn, t.signal);
			t.signal.aborted || n(e.media_sources);
		} catch (e) {
			t.signal.aborted || i(U(e));
		} finally {
			a.current = null, x(e, !1);
		}
	};
	return t ? /* @__PURE__ */ K("section", {
		class: "configfieldset",
		"aria-labelledby": "configMountsTitle",
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K(tr, { html: p("configMountsTitle", "挂载状态") }),
				/* @__PURE__ */ K("dl", {
					class: "configfacts",
					children: t.map((e) => /* @__PURE__ */ K(F, { children: [/* @__PURE__ */ K("dt", { children: [/* @__PURE__ */ K("span", {
						"aria-hidden": "true",
						dangerouslySetInnerHTML: { __html: b(s[e.location]) }
					}), {
						local: "本地磁盘",
						115: "CloudDrive · 115",
						pikpak: "CloudDrive · PikPak"
					}[e.location] || e.location] }), /* @__PURE__ */ K("dd", { children: [
						e.path || "未配置挂载点",
						" ",
						/* @__PURE__ */ K("span", {
							class: `configstatus ${e.online === !0 ? "online" : e.online === !1 ? "offline" : "unknown"}`,
							children: e.online === !0 ? "在线" : e.online === !1 ? "离线" : "未检测"
						})
					] })] }))
				}),
				r ? /* @__PURE__ */ K("p", {
					class: "configbad",
					role: "alert",
					children: r
				}) : null
			]
		}), /* @__PURE__ */ K("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ K("button", {
				type: "button",
				class: "geist-button",
				onClick: (e) => o(e.currentTarget),
				children: "刷新挂载状态"
			})
		})]
	}) : null;
}
function ar({ value: e, label: t, onChange: n }) {
	return /* @__PURE__ */ K(Mn, {
		value: e,
		label: t,
		onChange: n,
		className: "configsourcecontrol",
		options: [
			["local", "本地磁盘"],
			["115", "CloudDrive · 115"],
			["pikpak", "CloudDrive · PikPak"]
		].map(([e, t]) => [
			e,
			t,
			s[e] || e || "database"
		])
	});
}
function or({ data: e, receipt: t }) {
	let n = e.media_sources?.filter((e) => [
		"local",
		"115",
		"pikpak"
	].includes(e.location)), [r, i] = z(n?.length ? n.map((e) => e.path) : e.media_dirs.length ? e.media_dirs : [""]), [a, o] = z(n?.map((e) => e.location) ?? []), [s, c] = z(n?.map((e) => e.root) ?? []), [l, u] = z(n?.map((e) => e.library || "") ?? []), [d, f] = z(n?.map((e) => e.library_icon || "") ?? []), [m, h] = z(String(e.port)), [_, v] = z(!1), [y, b] = z([]), [S, C] = z(""), [w, T] = z(""), [E, D] = z(null), [O, k] = z(null), A = H(!1), ee = H(e.revision), te = H([]), j = H(null);
	V(() => {
		O !== null && (te.current[O]?.focus(), k(null));
	}, [O]), B(() => {
		if (!E) return;
		let e = setTimeout(() => location.assign(E.url), $n);
		return () => clearTimeout(e);
	}, [E]);
	let M = (e, t) => {
		i((n) => n.map((n, r) => r === e ? t : n));
	}, ne = () => {
		k(r.length), i((e) => [...e, ""]);
	}, N = (e) => {
		o((t) => t.filter((t, n) => n !== e)), c((t) => t.filter((t, n) => n !== e)), u((t) => t.filter((t, n) => n !== e)), f((t) => t.filter((t, n) => n !== e)), i((t) => t.filter((t, n) => n !== e)), b((t) => t.filter((t, n) => n !== e));
	}, re = (e, t) => {
		b((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, ie = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			x(t, !0);
			try {
				let { path: t } = await G(Qn, { initial: r[e] ?? "" });
				t && (M(e, t), re(e, ""));
			} catch (t) {
				re(e, U(t));
			} finally {
				x(t, !1);
			}
		}
	};
	return E ? /* @__PURE__ */ K("div", {
		class: "configsaved",
		role: "status",
		children: /* @__PURE__ */ K("div", {
			class: "geist-note geist-note-success",
			role: "note",
			children: [/* @__PURE__ */ K("svg", {
				"aria-hidden": "true",
				viewBox: "0 0 24 24",
				children: /* @__PURE__ */ K("use", { href: "#i-check" })
			}), /* @__PURE__ */ K("p", { children: /* @__PURE__ */ K("span", { children: [
				"配置已保存，Peach 正在重新启动。稍后自动跳转，或点击",
				/* @__PURE__ */ K("a", {
					href: E.url,
					children: "进入馆藏"
				}),
				"。"
			] }) })]
		})
	}) : /* @__PURE__ */ K("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configTitle",
		onSubmit: async (n) => {
			if (n.preventDefault(), !A.current) {
				A.current = !0, x(j.current, !0), T("");
				try {
					let n = await G(Zn, {
						revision: ee.current,
						media_dirs: r,
						...e.media_sources ? { media_sources: r.map((e, t) => ({
							path: e,
							location: a[t] || "local",
							root: s[t] || "",
							library: l[t] || "",
							library_icon: d[t] || ""
						})) } : {},
						port: m,
						scan_now: _
					});
					ee.current = n.revision, b([]), C(""), t("已保存配置"), D(n);
				} catch (e) {
					let t = nr(e);
					t ? (b(t.media_dirs ?? []), C(t.port ?? "")) : (b([]), C(""), T(U(e)));
				} finally {
					A.current = !1, x(j.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K(tr, { html: p("configTitle", "这台电脑") }),
				/* @__PURE__ */ K("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ K("span", {
							class: "configlabel",
							id: "configDirsLabel",
							children: "媒体文件夹"
						}),
						/* @__PURE__ */ K("div", {
							class: "configdirs",
							role: "group",
							"aria-labelledby": "configDirsLabel",
							children: r.map((t, n) => /* @__PURE__ */ K("div", {
								class: "configdir",
								children: [
									/* @__PURE__ */ K("span", {
										class: "configpathlabel",
										children: ["本机文件夹 ", n + 1]
									}),
									/* @__PURE__ */ K("input", {
										class: "geist-input",
										type: "text",
										value: t,
										"aria-label": `媒体文件夹 ${n + 1}`,
										"aria-invalid": y[n] ? "true" : void 0,
										onInput: (e) => M(n, e.currentTarget.value),
										ref: (e) => {
											te.current[n] = e;
										}
									}),
									/* @__PURE__ */ K("button", {
										type: "button",
										class: "geist-button configpick",
										"aria-label": "选择文件夹",
										onClick: (e) => ie(n, e.currentTarget),
										children: /* @__PURE__ */ K("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ K("use", { href: "#i-folder-search" })
										})
									}),
									r.length > 1 ? /* @__PURE__ */ K("button", {
										type: "button",
										class: "geist-button configrm danger",
										"aria-label": "移除这个文件夹",
										onClick: () => N(n),
										children: /* @__PURE__ */ K("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ K("use", { href: "#i-x" })
										})
									}) : null,
									/* @__PURE__ */ K("div", {
										class: "configsource",
										children: [
											/* @__PURE__ */ K("label", { children: ["媒体库名称", /* @__PURE__ */ K("input", {
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
											/* @__PURE__ */ K("div", {
												class: "configsourcelabel",
												children: ["媒体库图标", /* @__PURE__ */ K(Xn, {
													label: `媒体库图标 ${n + 1}`,
													value: d[n] || "",
													kind: a[n] || "local",
													onChange: (e) => {
														let t = [...d];
														t[n] = e, f(t);
													}
												})]
											}),
											/* @__PURE__ */ K("div", {
												class: "configsourcelabel",
												children: ["媒体来源", /* @__PURE__ */ K(ar, {
													label: `媒体来源 ${n + 1}`,
													value: a[n] || "local",
													onChange: (e) => {
														let t = [...a];
														t[n] = e, o(t);
													}
												})]
											}),
											e.windows === !1 ? /* @__PURE__ */ K("label", { children: ["Windows 中的对应路径", /* @__PURE__ */ K("input", {
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
									y[n] ? /* @__PURE__ */ K("p", {
										class: "configbad",
										role: "alert",
										children: y[n]
									}) : null
								]
							}, n))
						}),
						/* @__PURE__ */ K("button", {
							type: "button",
							class: "geist-button configadd",
							onClick: ne,
							children: "添加文件夹"
						}),
						a.some((e) => e === "115" || e === "pikpak") ? /* @__PURE__ */ K(qn, {}) : null,
						a.some((e) => e === "115" || e === "pikpak") ? e.mount_dependencies?.filter((e) => !e.available).map((e) => /* @__PURE__ */ K("p", {
							class: "confighelp",
							children: [
								"未检测到 ",
								e.name,
								"。",
								/* @__PURE__ */ K("a", {
									class: "externallink",
									href: e.download_url,
									target: "_blank",
									rel: "noreferrer",
									children: [
										"下载 ",
										e.name,
										/* @__PURE__ */ K("svg", {
											class: "externalmark",
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ K("use", { href: "#i-external-link" })
										})
									]
								})
							]
						})) : null,
						e.windows === !1 ? /* @__PURE__ */ K("p", {
							class: "confighelp",
							children: "本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\\ 对应本机挂载文件夹。"
						}) : null
					]
				}),
				e.port_editable === !1 ? null : /* @__PURE__ */ K("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ K("label", {
							for: "configPort",
							children: "本机访问端口"
						}),
						/* @__PURE__ */ K("input", {
							id: "configPort",
							class: "geist-input",
							type: "text",
							inputMode: "numeric",
							value: m,
							"aria-invalid": S ? "true" : void 0,
							onInput: (e) => h(e.currentTarget.value)
						}),
						S ? /* @__PURE__ */ K("p", {
							class: "configbad",
							role: "alert",
							children: S
						}) : null,
						/* @__PURE__ */ K("p", {
							class: "confighelp",
							children: "浏览器地址里冒号后面的数字，一般不用改。"
						})
					]
				}),
				/* @__PURE__ */ K("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ K("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ K("input", {
							type: "checkbox",
							checked: _,
							onChange: (e) => v(e.currentTarget.checked)
						}), /* @__PURE__ */ K("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ K("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ K("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ K("span", { children: "保存后扫描并补全资料" })]
				}),
				w ? /* @__PURE__ */ K(tr, { html: g(w, {
					variant: "error",
					label: "没有保存"
				}) }) : null
			]
		}), /* @__PURE__ */ K("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [/* @__PURE__ */ K("p", { children: e.port_editable === !1 ? "保存后 Peach 会重新载入配置。" : "保存后 Peach 会重新启动，端口改了就用新地址打开。" }), /* @__PURE__ */ K("button", {
				type: "submit",
				class: "geist-button primary",
				ref: j,
				children: "保存配置"
			})]
		})]
	});
}
function sr({ receipt: e, data: t, error: n }) {
	return n || !t ? /* @__PURE__ */ K(tr, {
		class: "configpage",
		html: g(n || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		})
	}) : /* @__PURE__ */ K("div", {
		class: "configpage",
		children: [
			t.startup ? /* @__PURE__ */ K("h2", {
				class: "configgroup",
				children: "通用"
			}) : null,
			t.startup ? /* @__PURE__ */ K(Un, {
				startup: t.startup,
				receipt: e
			}) : null,
			/* @__PURE__ */ K("h2", {
				class: "configgroup",
				children: "媒体"
			}),
			t.editable ? /* @__PURE__ */ K(or, {
				data: t,
				receipt: e
			}) : /* @__PURE__ */ K(tr, { html: g(t.notice, {
				variant: "secondary",
				label: "只读"
			}) }),
			/* @__PURE__ */ K(ir, { data: t }),
			t.peach_proxy || t.access ? /* @__PURE__ */ K("h2", {
				class: "configgroup",
				children: "网络与访问"
			}) : null,
			t.peach_proxy ? /* @__PURE__ */ K(Bn, {
				initial: t.peach_proxy,
				receipt: e
			}) : null,
			t.access ? /* @__PURE__ */ K(In, {
				initial: t.access,
				receipt: e
			}) : null,
			/* @__PURE__ */ K("h2", {
				class: "configgroup",
				children: "更新与维护"
			}),
			t.automatic_updates ? /* @__PURE__ */ K(zn, {
				initial: t.automatic_updates,
				receipt: e
			}) : null,
			t.updates ? /* @__PURE__ */ K(Rn, {
				initial: t.updates,
				initialJob: t.update_job
			}) : null,
			/* @__PURE__ */ K(rr, { facts: t.facts }),
			t.uninstall ? /* @__PURE__ */ K(Gn, { uninstall: t.uninstall }) : null
		]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var cr = Symbol.for("preact-signals");
function lr() {
	if (Y > 1) Y--;
	else {
		var e, t = !1;
		for ((function() {
			var e = _r;
			for (_r = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); pr !== void 0;) {
			var n = pr;
			for (pr = void 0, mr++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && xr(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (mr = 0, Y--, t) throw e;
	}
}
function ur(e) {
	if (Y > 0) return e();
	gr = ++hr, Y++;
	try {
		return e();
	} finally {
		lr();
	}
}
var dr, J = void 0;
function fr(e) {
	var t = J, n = dr;
	J = void 0, dr = void 0;
	try {
		return e();
	} finally {
		J = t, dr = n;
	}
}
var pr = void 0, Y = 0, mr = 0, hr = 0, gr = 0, _r = void 0, vr = 0;
function yr(e) {
	if (J !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== J) return t = {
			i: 0,
			S: e,
			p: J.s,
			n: void 0,
			t: J,
			e: void 0,
			x: void 0,
			r: t
		}, J.s !== void 0 && (J.s.n = t), J.s = t, e.n = t, 32 & J.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = J.s, t.n = void 0, J.s.n = t, J.s = t), t;
	}
}
function X(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
X.prototype.brand = cr, X.prototype.h = function() {
	return !0;
}, X.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? fr(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, X.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && fr(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, X.prototype.subscribe = function(e) {
	var t = this;
	return Ar(function() {
		var n = t.value;
		fr(function() {
			return e(n);
		});
	}, { name: "sub" });
}, X.prototype.valueOf = function() {
	return this.value;
}, X.prototype.toString = function() {
	return this.value + "";
}, X.prototype.toJSON = function() {
	return this.value;
}, X.prototype.peek = function() {
	var e = this;
	return fr(function() {
		return e.value;
	});
}, Object.defineProperty(X.prototype, "value", {
	get: function() {
		var e = yr(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (mr > 100) throw Error("Cycle detected");
			(function(e) {
				Y !== 0 && mr === 0 && e.l !== gr && (e.l = gr, _r = {
					S: e,
					v: e.v,
					i: e.i,
					o: _r
				});
			})(this), this.v = e, this.i++, vr++, Y++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				lr();
			}
		}
	}
});
function br(e, t) {
	return new X(e, t);
}
function xr(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function Sr(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function Cr(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function wr(e, t) {
	X.call(this, void 0, t), this.x = e, this.s = void 0, this.g = vr - 1, this.f = 4;
}
wr.prototype = new X(), wr.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === vr)) return !0;
	if (this.g = vr, this.f |= 1, this.i > 0 && !xr(this)) return this.f &= -2, !0;
	var e = J;
	try {
		Sr(this), J = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return J = e, Cr(this), this.f &= -2, !0;
}, wr.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	X.prototype.S.call(this, e);
}, wr.prototype.U = function(e) {
	if (this.t !== void 0 && (X.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, wr.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(wr.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = yr(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function Tr(e, t) {
	return new wr(e, t);
}
function Er(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		Y++;
		var n = J;
		J = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, Dr(e), t;
		} finally {
			J = n, lr();
		}
	}
}
function Dr(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, Er(e);
}
function Or(e) {
	if (J !== this) throw Error("Out-of-order effect");
	Cr(this), J = e, this.f &= -2, 8 & this.f && Dr(this), lr();
}
function kr(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, dr && dr.push(this);
}
kr.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, kr.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, Er(this), Sr(this), Y++;
	var e = J;
	return J = this, Or.bind(this, e);
}, kr.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = pr, pr = this);
}, kr.prototype.d = function() {
	this.f |= 8, 1 & this.f || Dr(this);
}, kr.prototype.dispose = function() {
	this.d();
};
function Ar(e, t) {
	var n = new kr(e, t);
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
var jr, Mr, Nr = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, Pr = [];
Ar(function() {
	jr = this.N;
})();
function Fr(e, t) {
	T[e] = t.bind(null, T[e] || function() {});
}
function Ir(e) {
	if (Mr) {
		var t = Mr;
		Mr = void 0, t();
	}
	Mr = e && e.S();
}
function Lr(e) {
	var t = this, n = e.data, r = zr(n);
	r.name = "ReactiveDom", r.value = n;
	var i = rt(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = Tr(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = Tr(function() {
			return !Array.isArray(i.value) && !D(i.value);
		}), o = Ar(function() {
			if (this.N = Hr, a.value) {
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
Lr.displayName = "ReactiveTextNode", Object.defineProperties(X.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: Lr
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
}), Fr("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof X && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), Fr("__r", function(e, t) {
	if (e(t), t.type !== F) {
		Ir();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return Ar(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				Nr && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), Ir(n);
	}
}), Fr("__e", function(e, t, n, r) {
	Ir(), e(t, n, r);
}), Fr("diffed", function(e, t) {
	Ir();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = Rr(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function Rr(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = br(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: Ar(function() {
			this.N = Hr;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
Fr("unmount", function(e, t) {
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
}), Fr("__h", function(e, t, n, r) {
	r < 3 && (t.__$f |= 2), e(t, n, r);
}), fe.prototype.shouldComponentUpdate = function(e, t) {
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
function zr(e, t) {
	return rt(function() {
		return br(e, t);
	}, []);
}
var Br = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function Vr() {
	ur(function() {
		for (var e; e = Pr.shift();) jr.call(e);
	});
}
function Hr() {
	Pr.push(this) === 1 && (T.requestAnimationFrame || Br)(Vr);
}
//#endregion
//#region src/state/quality-goals.ts
var Ur = "/api/quality-goals?limit=200", Wr = {
	data: null,
	error: ""
}, Gr = br(Wr), Kr = 0, qr = Tr(() => Gr.value);
Tr(() => Gr.value.data?.total ?? null);
function Jr() {
	Kr += 1, Gr.value = Wr;
}
async function Yr(e) {
	let t = Kr += 1;
	try {
		let n = await W(Ur, e);
		return t === Kr && (Gr.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === Kr && (Gr.value = {
			data: null,
			error: U(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var Xr = (e, t) => Yr(t), Zr = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function Qr({ openItem: t, javTitleHtml: i, javDisplayName: a, srcBadge: o }) {
	let { data: s, error: c } = qr.value;
	if (c) return /* @__PURE__ */ K("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: g(c, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let l = s?.items ?? [];
	return l.length ? /* @__PURE__ */ K("div", {
		class: "quality-workspace",
		children: [/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: u("待升级", `${s?.total ?? l.length} 部作品`) } }), /* @__PURE__ */ K("div", {
			class: "qualitylist",
			children: l.map((s) => /* @__PURE__ */ K("article", {
				class: "qualityitem",
				children: [
					/* @__PURE__ */ K("button", {
						class: "qualitycover",
						type: "button",
						"aria-label": `打开 ${a(s)}`,
						onClick: () => t(s.id),
						children: [/* @__PURE__ */ K("span", {
							class: "qualityfallback",
							children: "暂无预览"
						}), /* @__PURE__ */ K("img", {
							src: Zr(s),
							alt: "",
							loading: "lazy",
							onError: (e) => e.currentTarget.remove()
						})]
					}),
					/* @__PURE__ */ K("div", {
						class: "qualitybody",
						children: [
							/* @__PURE__ */ K("h3", { children: /* @__PURE__ */ K("button", {
								type: "button",
								"data-middle-truncate": !0,
								onClick: () => t(s.id),
								dangerouslySetInnerHTML: { __html: i(s) }
							}) }),
							/* @__PURE__ */ K("p", {
								class: "mono",
								children: [
									/* @__PURE__ */ K("span", {
										style: "display:contents",
										dangerouslySetInnerHTML: { __html: o(s.location, s.cost) }
									}),
									/* @__PURE__ */ K("span", { children: e[s.location] ?? s.location }),
									/* @__PURE__ */ K("span", { children: n(s.duration) }),
									/* @__PURE__ */ K("span", { children: r(s.size ?? 0) })
								]
							}),
							s.reason ? /* @__PURE__ */ K("p", {
								class: "qualityreason",
								children: s.reason
							}) : null
						]
					}),
					/* @__PURE__ */ K("footer", {
						class: "qualityactions",
						children: /* @__PURE__ */ K("button", {
							type: "button",
							class: "geist-button",
							onClick: () => t(s.id),
							children: "查看版本"
						})
					})
				]
			}, s.id))
		})]
	}) : /* @__PURE__ */ K("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: f("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/islands/scraping.tsx
var $r = (e, t) => W("/api/scraping", t);
function ei({ value: e, onChange: t }) {
	let n = H(null), r = H(t);
	return r.current = t, V(() => {
		let t = n.current;
		t.innerHTML = y([["peach", "Peach 代理"], ["direct", "直接连接"]], e, { label: "连接方式" });
		let i = C(t.firstElementChild), a = () => r.current(i.value);
		return i.addEventListener("change", a), () => {
			i.disabled = !0, i.removeEventListener("change", a), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ K("div", {
		ref: n,
		class: "scraping-network"
	});
}
function ti({ source: e, toast: t }) {
	let [n, r] = z(e), [i, a] = z(e.network), [s, c] = z(""), [l, u] = z(""), [d, f] = z("paste"), [m, h] = z(""), [_, v] = z(!1), [y, b] = z(""), [S, C] = z([]), w = H(null), T = H(null);
	V(() => {
		T.current?.querySelectorAll("footer button").forEach((e) => x(e, _));
	}, [_]);
	let E = H(new AbortController());
	B(() => () => E.current.abort(), []);
	async function D(n) {
		if (!_) {
			v(!0), b(""), C([]);
			try {
				if (n === "check") {
					let t = await G("/api/scraping/check", { source: e.source }, "POST", E.current.signal);
					E.current.signal.aborted || C(t.results);
				} else {
					let a = await G("/api/scraping/settings", {
						source: e.source,
						network: i,
						cookie: s,
						cookies_text: l,
						revoke: n === "revoke"
					}, "POST", E.current.signal);
					E.current.signal.aborted || (r(a.saved), c(""), u(""), h(""), w.current && (w.current.value = ""), t(n === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				E.current.signal.aborted || b(U(e));
			} finally {
				E.current.signal.aborted || v(!1);
			}
		}
	}
	return /* @__PURE__ */ K("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ K("form", {
			ref: T,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), D("save");
			},
			children: [/* @__PURE__ */ K("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ K("div", {
						class: "geist-fieldset-heading",
						children: [/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: p(`scraping-${e.source}`, e.label) } }), /* @__PURE__ */ K("a", {
							class: "scraping-url externallink",
							href: e.login,
							target: "_blank",
							rel: "noopener noreferrer",
							children: [
								/* @__PURE__ */ K("img", {
									src: o({ source: e.source }),
									alt: "",
									width: "16",
									height: "16",
									loading: "lazy",
									onError: (e) => e.currentTarget.remove()
								}),
								/* @__PURE__ */ K("span", { children: e.login }),
								/* @__PURE__ */ K("svg", {
									class: "externalmark",
									viewBox: "0 0 24 24",
									"aria-hidden": "true",
									children: /* @__PURE__ */ K("use", { href: "#i-external-link" })
								})
							]
						})]
					}),
					/* @__PURE__ */ K("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ K(ei, {
							value: i,
							onChange: a
						})]
					}),
					i === "peach" && /* @__PURE__ */ K(_t, {
						href: "/configuration#peachProxy",
						children: "配置 Peach 代理"
					}),
					e.accepts_cookie && /* @__PURE__ */ K(F, { children: [
						/* @__PURE__ */ K("p", { children: n.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ K("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ K("label", { children: [/* @__PURE__ */ K("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: d === t,
								onChange: () => {
									f(t), c(""), u(""), h("");
								}
							}), /* @__PURE__ */ K("span", { children: n })] }, t))
						}),
						d === "paste" ? /* @__PURE__ */ K("label", { children: ["Cookie", /* @__PURE__ */ K("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: s,
							disabled: _,
							onInput: (e) => c(e.currentTarget.value)
						})] }) : /* @__PURE__ */ K("label", {
							class: "scraping-file",
							children: ["Netscape Cookie 文件（.txt）", /* @__PURE__ */ K("span", {
								class: "scraping-file-control",
								children: [
									/* @__PURE__ */ K("span", {
										class: "geist-button",
										children: "选择文件"
									}),
									/* @__PURE__ */ K("span", {
										class: "scraping-file-name",
										children: m || "未选择文件"
									}),
									/* @__PURE__ */ K("input", {
										ref: w,
										type: "file",
										accept: ".txt",
										disabled: _,
										onChange: async (e) => {
											let t = e.currentTarget.files?.[0];
											if (!t) {
												u(""), h("");
												return;
											}
											if (u(""), t.size > 262144) {
												b("Cookie 文本超过 256 KiB"), e.currentTarget.value = "";
												return;
											}
											v(!0);
											try {
												let e = await t.text();
												E.current.signal.aborted || (u(e), h(t.name));
											} catch {
												E.current.signal.aborted || b("Cookie 文件未读取，请重新选择");
											} finally {
												E.current.signal.aborted || v(!1);
											}
										}
									})
								]
							})]
						})
					] }),
					y && /* @__PURE__ */ K("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: g(y, { variant: "error" }) }
					}),
					S.map((t) => /* @__PURE__ */ K("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: g(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ K("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					e.accepts_cookie && n.cookie_saved && /* @__PURE__ */ K("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void D("revoke"),
						children: "撤销 Cookie"
					}),
					/* @__PURE__ */ K("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void D("check"),
						children: "检查连接"
					}),
					/* @__PURE__ */ K("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					})
				]
			})]
		})
	});
}
function ni({ data: e, error: t, toast: n }) {
	let [r, i] = z(""), [a, o] = z(!1), [s, c] = z(""), [l, u] = z(""), d = H(null);
	V(() => x(d.current, a), [a]);
	let f = H(new AbortController()), h = H(0);
	async function _(e = !1) {
		let t = ++h.current;
		await mt({
			read: (e) => W("/api/scraping/cover", e),
			active: () => !f.current.signal.aborted && t === h.current,
			render: (t) => {
				o(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && c(t.error || "采集未取得"), t.status === "complete" && !e && (u(t.result || "封面采集完成"), n(t.result || "封面采集完成"));
			},
			disconnected: () => c("连接中断，正在重新读取后台进度")
		});
	}
	B(() => (_(!0), () => f.current.abort()), []);
	async function v() {
		if (!a) {
			h.current++, o(!0), c(""), u("");
			try {
				await G("/api/scraping/cover", { code: r }, "POST", f.current.signal), await _();
			} catch (e) {
				f.current.signal.aborted || (o(!1), c(U(e)));
			}
		}
	}
	return t ? /* @__PURE__ */ K("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: g(t, { variant: "error" }) }
	}) : /* @__PURE__ */ K("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ K("p", { children: "高清图片可能需要代理才能下载，请先检查连接。" }),
			/* @__PURE__ */ K("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ K("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: p("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ K("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), v();
							},
							children: [/* @__PURE__ */ K("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: r,
								disabled: a,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => i(e.currentTarget.value)
							}), /* @__PURE__ */ K("button", {
								ref: d,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						a && /* @__PURE__ */ K("div", {
							"aria-live": "polite",
							dangerouslySetInnerHTML: { __html: m("正在抓取封面") }
						}),
						s && /* @__PURE__ */ K("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: g(s, { variant: "error" }) }
						}),
						l && /* @__PURE__ */ K("div", {
							role: "status",
							dangerouslySetInnerHTML: { __html: g(l) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ K(ti, {
				source: e,
				toast: n
			}, e.source))
		]
	});
}
//#endregion
//#region src/islands/activity.tsx
var ri = (e, t) => W("/api/tasks", t), ii = {
	manual: "手动",
	scheduled: "定时",
	startup: "启动",
	cli: "命令行"
}, ai = {
	pending: "排队中",
	running: "进行中",
	succeeded: "已完成",
	failed: "失败",
	cancelled: "已取消",
	interrupted: "被打断"
}, oi = (e) => ai[e] || e, si = {
	succeeded: "ok",
	failed: "error",
	cancelled: "paused",
	interrupted: "paused"
}, ci = {
	checked: "已检查",
	total: "总数",
	scanned: "已扫描",
	identified: "已识别",
	candidates: "资料候选",
	covers: "封面",
	changed: "已改动",
	operation: "操作",
	ok: "取得",
	miss: "未取得",
	kept: "保留",
	planned: "计划",
	done: "已处理",
	added: "新增",
	written: "已写入",
	removed: "已移除",
	exit_code: "退出码",
	issue_count: "问题"
};
function li(e) {
	if (typeof e != "number" || !Number.isFinite(e) || e < 0) return "";
	let t = Math.floor(e);
	if (t < 60) return `${t} 秒`;
	let n = Math.floor(t / 60);
	return n < 60 ? `${n} 分 ${t % 60} 秒` : `${Math.floor(n / 60)} 小时 ${n % 60} 分`;
}
function ui(e) {
	if (!e) return "";
	let t = new Date(e);
	return Number.isNaN(t.getTime()) ? "" : t.toLocaleString(void 0, {
		month: "2-digit",
		day: "2-digit",
		hour: "2-digit",
		minute: "2-digit"
	});
}
function di(e) {
	return Object.entries(e || {}).filter(([e, t]) => e !== "blocked_by" && (typeof t == "number" || typeof t == "string") && String(t) !== "").map(([e, t]) => `${ci[e] || e} ${t}`).join(" · ");
}
function fi({ status: e }) {
	let t = si[e];
	return /* @__PURE__ */ K("span", {
		class: t ? `sbadge ${t}` : "sbadge",
		children: [/* @__PURE__ */ K("i", { "aria-hidden": "true" }), oi(e)]
	});
}
function pi({ run: e, meta: t, children: n, footer: r }) {
	return /* @__PURE__ */ K("li", { children: /* @__PURE__ */ K("section", {
		class: "cleanupfieldset activity-run",
		"data-geist-fieldset": !0,
		"data-status": e.status,
		"data-task-key": e.task_key,
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K("div", {
					class: "activity-run-head",
					children: [/* @__PURE__ */ K("strong", { children: e.task_label }), /* @__PURE__ */ K(fi, { status: e.status })]
				}),
				/* @__PURE__ */ K("p", {
					class: "cleanupmeta",
					children: t
				}),
				n
			]
		}), r ? /* @__PURE__ */ K("div", {
			class: "geist-fieldset-footer",
			children: /* @__PURE__ */ K("p", { children: r })
		}) : null]
	}) });
}
function mi({ run: e }) {
	let t = e.progress_total || 0, n = e.progress_current || 0, r = e.progress_label || "正在进行", i = li(e.elapsed_seconds);
	return /* @__PURE__ */ K(pi, {
		run: e,
		meta: [ii[e.trigger] || e.trigger, i && `已跑 ${i}`].filter(Boolean).join(" · "),
		children: t > 0 ? /* @__PURE__ */ K("div", {
			class: "activity-progress",
			children: [/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: _(r, n, t) } }), /* @__PURE__ */ K("p", {
				class: "cleanupmeta",
				children: [
					r,
					" · ",
					n,
					" / ",
					t,
					" 项"
				]
			})]
		}) : /* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: m(r) } })
	});
}
function hi({ run: e }) {
	let t = di(e.result_summary), n = li(e.elapsed_seconds);
	return /* @__PURE__ */ K(pi, {
		run: e,
		meta: [
			ii[e.trigger] || e.trigger,
			ui(e.finished_at),
			n && `用时 ${n}`
		].filter(Boolean).join(" · "),
		footer: e.error,
		children: t ? /* @__PURE__ */ K("p", {
			class: "cleanupmeta",
			children: t
		}) : null
	});
}
function gi({ data: e, error: t, preview: n }) {
	let [r, i] = z(e), [a, o] = z(t), s = H(new AbortController()), c = r?.running || [];
	if (B(() => {
		if (n) return;
		let e = s.current.signal, t = 0, r = async () => {
			try {
				let n = await W("/api/tasks", e);
				if (e.aborted) return;
				i(n), o(""), t = setTimeout(r, n.running.length ? 2e3 : 1e4);
			} catch (n) {
				if (e.aborted) return;
				o(U(n)), t = setTimeout(r, 1e4);
			}
		};
		return t = setTimeout(r, c.length ? 2e3 : 1e4), () => {
			s.current.abort(), clearTimeout(t);
		};
	}, []), !r) return /* @__PURE__ */ K("div", {
		class: "activitypage",
		role: "alert",
		dangerouslySetInnerHTML: { __html: g(a || "读取任务中心失败", {
			variant: "error",
			filled: !0
		}) }
	});
	let l = r.skipped || [], u = (r.finished || []).filter((e) => !l.some((t) => t.id === e.id)), d = !c.length && !l.length && !u.length;
	return /* @__PURE__ */ K("div", {
		class: "activitypage",
		children: [
			a && /* @__PURE__ */ K("div", {
				role: "alert",
				dangerouslySetInnerHTML: { __html: g(a, {
					variant: "error",
					filled: !0
				}) }
			}),
			r.available === !1 && /* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: g(r.message || "账本上还没有任务中心的表", { variant: "warning" }) } }),
			d ? /* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: f("history", "还没有任务记录", "扫描、追更检查、批量操作和命令行批处理跑起来之后，这里会显示它们的进度与结果。") } }) : /* @__PURE__ */ K(F, { children: [
				/* @__PURE__ */ K("section", {
					class: "activitysection",
					"aria-labelledby": "activityRunning",
					children: [/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: p("activityRunning", "正在进行") } }), c.length ? /* @__PURE__ */ K("ul", {
						class: "activity-runs",
						"aria-live": "polite",
						children: c.map((e) => /* @__PURE__ */ K(mi, { run: e }, e.id))
					}) : /* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: g("没有任务在跑。", {
						variant: "secondary",
						size: "small"
					}) } })]
				}),
				!!l.length && /* @__PURE__ */ K("section", {
					class: "activitysection",
					"aria-labelledby": "activitySkipped",
					children: [/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: p("activitySkipped", "被挡下的") } }), /* @__PURE__ */ K("ul", {
						class: "activity-runs",
						children: l.map((e) => /* @__PURE__ */ K(hi, { run: e }, e.id))
					})]
				}),
				!!u.length && /* @__PURE__ */ K("section", {
					class: "activitysection",
					"aria-labelledby": "activityFinished",
					children: [/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: p("activityFinished", "最近完成") } }), /* @__PURE__ */ K("ul", {
						class: "activity-runs",
						children: u.map((e) => /* @__PURE__ */ K(hi, { run: e }, e.id))
					})]
				})
			] })
		]
	});
}
//#endregion
//#region src/state/index.ts
var _i = { "quality-goals": {
	refresh: Yr,
	reset: Jr
} }, vi = () => Object.keys(_i);
async function yi(e) {
	let t = _i[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/review-evidence.ts
var bi = (e = "") => /^https?:\/\//i.test(e) ? e : "";
function xi(e = "") {
	let n = bi(e) || (e.startsWith("/") && !e.startsWith("//") ? e : "");
	return `<div class="reviewimage" data-review-picture><span class="reviewimageempty"${n ? " hidden" : ""}>未取得来源图片</span>${n ? `<img src="${t(n)}" alt="来源候选图片" loading="lazy">` : ""}</div>`;
}
function Si(e) {
	let n = bi(e.profile_url), r = (e.preview_assets || []).slice(0, 6), i = Math.max(0, Number(e.video_count || e.videos || 0));
	return `<section class="reviewidentityevidence"><h5>候选身份：${t(e.babepedia_name || "未标注")}</h5>
    <div class="reviewevidenceactions">${n ? `<a class="geist-button externallink" href="${t(n)}" target="_blank" rel="noopener noreferrer">来源资料<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a>` : ""}
    <button type="button" class="geist-button" data-entity-kind="creator" data-entity-name="${t(e.creator || "")}">查看全部 ${i.toLocaleString()} 部作品</button></div>
    ${xi(e.preview_url)}
    <p>通过后记录身份判断。</p>
    ${r.length ? `<h5>本地作品样本</h5><div class="reviewevidencesamples">${r.map((e) => `<div class="reviewevidencesample">
      <button class="geist-button" type="button" data-review-open-item="${e.id}"><span data-middle-truncate title="${t(e.name)}">${t(e.name)}</span></button>
      <button class="geist-button" type="button" data-review-reveal="${e.id}" aria-label="打开 ${t(e.name)} 的文件位置">文件位置</button>
    </div>`).join("")}</div>` : "<p>暂无本地作品样本，打开全部作品核对。</p>"}</section>`;
}
function Ci(e) {
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
//#region src/selection.ts
function wi(e, t, n, r, i, a = i || !e.has(r)) {
	let o = n === null ? -1 : t.indexOf(n), s = t.indexOf(r);
	return i && o >= 0 && s >= 0 ? t.slice(Math.min(o, s), Math.max(o, s) + 1).forEach((t) => e.add(t)) : a ? e.add(r) : e.delete(r), r;
}
function Ti(e, t) {
	let n = t.filter((t) => e.has(t)).length;
	return {
		count: n,
		all: n > 0 && n === t.length,
		mixed: n > 0 && n < t.length
	};
}
function Ei(e, t, n) {
	t.forEach((t) => n ? e.add(t) : e.delete(t));
}
function Di({ count: e, label: t, all: n, summary: r, actions: i, locked: a = !1 }) {
	e && (e.textContent = t), n && (n.checked = r.all, n.indeterminate = r.mixed);
	for (let e of i) e.disabled = !r.count || a;
}
//#endregion
//#region src/review-bulk.ts
var Oi = () => ({
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
function ki(e) {
	let t = e?.querySelector(".reviewbulktoolbar");
	if (!e || !t || t.offsetParent === null) return;
	e.style.setProperty("--review-controls-height", `${t.getBoundingClientRect().height}px`);
	let n = [t, ...e.querySelectorAll(".reviewgroupbar")];
	for (let e of n) {
		let t = parseFloat(getComputedStyle(e).top);
		e.classList.toggle("is-stuck", e.offsetParent !== null && window.scrollY > 0 && Number.isFinite(t) && Math.abs(e.getBoundingClientRect().top - t) <= 1);
	}
	let r = n.filter((e) => e.classList.contains("is-stuck"));
	e.classList.toggle("review-is-stuck", r.length > 0);
	let i = r[0], a = r.at(-1);
	if (!i || !a) return;
	let o = i.getBoundingClientRect(), s = a.getBoundingClientRect();
	e.style.setProperty("--review-pane-left", `${o.left}px`), e.style.setProperty("--review-pane-width", `${o.width}px`), e.style.setProperty("--review-pane-height", `${s.bottom - o.top}px`);
}
function Ai(e, t) {
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
function ji(e, t) {
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
function Mi(e, t, n, r, i) {
	e.anchor = wi(e.selected, t, e.anchor, n, r, i);
}
async function Ni(e, t, n, r) {
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
				message: U(e)
			});
		}
	}
	return {
		completed: a,
		failures: i
	};
}
function Pi(e) {
	return e.length ? [...new Set(e.flatMap((e) => e.candidates?.map((e) => e.source || "") || []))].filter((t) => t && e.every((e) => e.candidates?.filter((e) => e.source === t).length === 1)) : [];
}
function Fi(e, t) {
	let n = e.querySelector(".reviewlist");
	if (!n || !t.rows.length || t.locked) return;
	let r = t.state, i = [...n.querySelectorAll("[data-review-key]")];
	t.category !== void 0 && r.category !== t.category && (r.category = t.category, r.filter = "", r.groupBy = "candidates", r.anchor = null);
	let a = t.catalog || t.rows, o = Ai(a, t.metadata);
	o.some((e) => e[0] === r.groupBy) || (r.groupBy = "candidates", r.filter = "");
	let s = ji(a, r.groupBy);
	s.some((e) => e.key === r.filter) || (r.filter = "");
	let c = () => [...n.querySelectorAll("[data-review-key]")].filter((e) => !e.closest("[hidden]")), u = () => c().filter((e) => r.selected.has(e.dataset.reviewKey)), d = () => t.rows.filter((e) => u().some((t) => t.dataset.reviewKey === e.item_key)), f = (e) => !e.querySelector("[data-review-status=\"approved\"]")?.disabled, p = (e, t = "") => {
		let n = document.createElement("button");
		return n.type = "button", n.className = `geist-button ${t}`.trim(), n.textContent = e, n;
	}, m = document.createElement("div");
	m.className = "reviewbulkbar reviewbulktoolbar", m.setAttribute("role", "group"), m.setAttribute("aria-label", "复核批量操作");
	let h = document.createElement("div");
	h.className = "reviewgroupby", h.innerHTML = y(o, r.groupBy, { label: "筛选分组方式" });
	let g = C(h.firstElementChild);
	h.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), g.addEventListener("change", () => {
		if (r.busy || !o.some((e) => e[0] === g.value)) return;
		r.groupBy = g.value, r.filter = "", r.anchor = null;
		let n = e.parentElement;
		t.refresh(), n?.querySelector(".reviewgroupby button")?.focus({ preventScroll: !0 });
	});
	let _ = document.createElement("div");
	_.className = "reviewcategoryfilter", _.hidden = s.length < 2, _.innerHTML = y([[
		"",
		"全部分类",
		"list-filter"
	], ...s.map((e) => [
		e.key,
		`${e.title} · ${e.rows.length}`,
		"list-filter"
	])], r.filter, { label: r.groupBy === "field" ? "筛选字段分类" : "筛选当前分类" });
	let v = _.querySelector("[data-select-menu]");
	if (v) {
		let e = document.createElement("div");
		e.setAttribute("role", "group"), e.setAttribute("aria-label", r.groupBy === "field" ? "字段分类" : "当前分类");
		let t = document.createElement("div");
		t.className = "reviewfilterheading", t.textContent = e.getAttribute("aria-label"), t.setAttribute("aria-hidden", "true"), e.append(t, ...Array.from(v.children).slice(1)), v.append(e);
	}
	let b = C(_.firstElementChild);
	_.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), b.addEventListener("change", () => {
		if (r.busy || b.value && !s.some((e) => e.key === b.value)) return;
		r.filter = b.value, r.anchor = null;
		let n = e.parentElement;
		t.refresh(), n?.querySelector(".reviewcategoryfilter button")?.focus({ preventScroll: !0 });
	});
	let S = p("全选本页"), w = p("通过所选", "primary"), T = p("拒绝所选", "error"), E = document.createElement("span");
	E.className = "reviewselectedcount selectiondockcount", E.setAttribute("role", "status");
	let D = document.createElement("div");
	D.className = "reviewbulksource", D.hidden = !t.metadata;
	let O = document.createElement("p");
	O.className = "reviewstate reviewbulkfeedback", O.setAttribute("role", "status");
	let k = document.createElement("div");
	k.className = "reviewbulkdecisions", k.append(w, T);
	let A = document.createElement("div");
	A.className = "selectiondock reviewdock", A.setAttribute("role", "group"), A.setAttribute("aria-label", "复核所选项目");
	let ee = p("取消选择");
	A.append(E, D, k, ee, O), m.append(h, _, S);
	let te = e.querySelector(".reviewcontrols");
	te ? te.after(m) : n.before(m), e.append(A), n.classList.add("reviewgroups");
	let j = () => {
		r.selected.clear(), r.anchor = null, N();
	};
	ee.onclick = () => {
		r.busy || (j(), S.focus({ preventScroll: !0 }));
	}, S.onclick = () => {
		if (r.busy) return;
		let e = c(), t = u().length === e.length;
		e.forEach((e) => t ? r.selected.delete(e.dataset.reviewKey) : r.selected.add(e.dataset.reviewKey)), N();
	}, w.onclick = () => re("approved", w), T.onclick = () => re("rejected", T);
	let M = [];
	for (let e of s) {
		let t = e.rows.map((e) => i.find((t) => t.dataset.reviewKey === e.item_key)).filter((e) => !!e);
		if (!t.length) continue;
		let a = document.createElement("section");
		a.className = "reviewgroup", a.hidden = !!r.filter && e.key !== r.filter;
		let o = document.createElement("div");
		o.className = "reviewbulkbar reviewgroupbar";
		let s = document.createElement("h3");
		s.textContent = `${e.title} · ${t.length}`;
		let u = p("全选本组"), d = document.createElement("div");
		d.className = "reviewlist", o.append(s, u), a.append(o, d), n.append(a), u.onclick = () => {
			if (r.busy) return;
			let e = t.map((e) => e.dataset.reviewKey);
			Ei(r.selected, e, !e.every((e) => r.selected.has(e))), N();
		}, M.push(() => {
			u.textContent = t.every((e) => r.selected.has(e.dataset.reviewKey)) ? "清空本组" : "全选本组";
		});
		for (let e of t) {
			d.append(e);
			let t = e.dataset.reviewKey;
			r.errors.has(t) && (e.querySelector(".reviewstate").textContent = r.errors.get(t));
			let n = e.querySelector("h4,.reviewentity b") || e, i = document.createElement("label");
			i.className = "reviewpickitem", i.innerHTML = l();
			let a = i.querySelector("input");
			if (a.setAttribute("aria-label", `选择 ${e.querySelector("legend")?.textContent || n.textContent || t}`), n !== e) {
				let e = document.createElement("span");
				e.className = "reviewpickname", e.append(...n.childNodes), n.classList.add("reviewpickheading"), n.append(i, e);
			} else e.prepend(i);
			let o = (e, n) => {
				Mi(r, c().map((e) => e.dataset.reviewKey), t, e, n), N();
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
						let i = c(), a = i[i.indexOf(e) + (n.key === "ArrowDown" ? 1 : -1)];
						a && (r.anchor === null && (r.anchor = t), Mi(r, i.map((e) => e.dataset.reviewKey), a.dataset.reviewKey, !0, !0), N(), a.querySelector(".reviewpickitem input")?.focus());
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
		r.busy || !e.contains(n) || (t.key === "Escape" && r.selected.size && (t.preventDefault(), t.stopPropagation(), j()), (t.ctrlKey || t.metaKey) && t.key.toLowerCase() === "a" && !t.target.matches("textarea,input:not([type=\"checkbox\"]):not([type=\"radio\"])") && (t.preventDefault(), t.stopPropagation(), c().forEach((e) => r.selected.add(e.dataset.reviewKey)), N()));
	});
	let ne = "";
	function N() {
		let e = u();
		S.textContent = e.length === c().length ? "清空当前选择" : r.filter ? "全选当前分类" : "全选本页", A.hidden = !e.length, Di({
			count: E,
			label: `已选 ${e.length} 项`,
			summary: Ti(r.selected, c().map((e) => e.dataset.reviewKey)),
			actions: [w, T]
		}), w.disabled ||= e.some((e) => !f(e));
		let n = Pi(d());
		D.hidden = !t.metadata || !d().some((e) => (e.candidates?.length || 0) > 1);
		let i = e.length && !n.length ? "所选项目无共同来源" : "统一选择来源", a = JSON.stringify([i, n]);
		if (a !== ne) {
			ne = a, D.innerHTML = y([["", i], ...n.map((e) => [e, e])], "", { label: "统一选择来源" });
			let e = C(D.firstElementChild);
			e.disabled = !n.length, e.addEventListener("change", () => {
				if (!(r.busy || !Pi(d()).includes(e.value))) {
					for (let n of u()) {
						let i = t.rows.find((e) => e.item_key === n.dataset.reviewKey).candidates.find((t) => t.source === e.value);
						n.querySelectorAll("input[type=\"radio\"]").forEach((e) => {
							e.checked = e.value === i.candidate_key;
						}), r.choices.set(n.dataset.reviewKey, i.candidate_key);
					}
					O.textContent = `已选择 ${e.value}，点击通过所选采用。`;
				}
			});
		}
		M.forEach((e) => e());
	}
	async function re(n, i) {
		if (r.busy || !u().length) return;
		let a = u().map((e) => ({
			key: e.dataset.reviewKey,
			payload: {
				...t.payload(e),
				status: n
			}
		}));
		if (n === "approved" && t.metadata && a.some((e) => !e.payload.candidate_key)) {
			O.textContent = "请先为所选的多来源候选选择来源。", u().find((e) => !e.querySelector("input[type=\"radio\"]:checked"))?.querySelector("input[type=\"radio\"]")?.focus();
			return;
		}
		r.busy = !0, O.textContent = `正在处理 0 / ${a.length}`, x(i, !0);
		let o = [...e.querySelectorAll("button,input")], s = o.map((e) => e.getAttribute("aria-disabled"));
		o.forEach((e) => e.setAttribute("aria-disabled", "true"));
		let c = (e) => {
			e instanceof KeyboardEvent && e.key === "Tab" || (e.preventDefault(), e.stopImmediatePropagation());
		};
		e.addEventListener("click", c, !0), e.addEventListener("keydown", c, !0);
		let l = 0, d = await Ni(a, async (e) => {
			try {
				return await t.submit(e);
			} finally {
				l++, t.active() && (O.textContent = `正在处理 ${l} / ${a.length}`);
			}
		}, (e) => {
			r.selected.delete(e), r.errors.delete(e), t.applied(e);
		}, t.active);
		if (r.busy = !1, e.removeEventListener("click", c, !0), e.removeEventListener("keydown", c, !0), o.forEach((e, t) => {
			let n = s[t];
			n === null ? e.removeAttribute("aria-disabled") : e.setAttribute("aria-disabled", n);
		}), x(i, !1), !t.active()) return;
		t.notify(`已${n === "approved" ? "通过" : "拒绝"} ${d.completed} 项${d.failures.length ? `，${d.failures.length} 项未完成` : ""}`), d.failures.forEach((e) => r.errors.set(e.key, e.message));
		let f = e.parentElement;
		t.refresh(), f?.querySelector(".reviewbulktoolbar button")?.focus({ preventScroll: !0 });
	}
	N(), ki(e);
}
function Ii(e, t, n = 1) {
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
function Li(e, t) {
	return Math.max(1, Math.ceil(e / t));
}
function Ri(e, t) {
	return Math.min(Math.max(1, Math.floor(e) || 1), t);
}
function zi(e, t, n) {
	if (t <= 1) return "";
	let r = Ii(e, t).map((t) => t === "…" ? "<li class=\"board-page-dots\" aria-hidden=\"true\">…</li>" : `<li><button type="button" class="board-page" data-page="${t}" aria-label="第 ${t} 页"${t === e ? " aria-current=\"page\"" : ""}>${t}</button></li>`).join("");
	return `<nav class="board-pagination" aria-label="${n}">
    <button type="button" class="geist-button" data-page="${e - 1}"${e <= 1 ? " disabled" : ""}><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-left"></use></svg>上一页</button>
    <ul>${r}</ul>
    <button type="button" class="geist-button" data-page="${e + 1}"${e >= t ? " disabled" : ""}>下一页<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"></use></svg></button>
  </nav>`;
}
//#endregion
//#region src/native-image.ts
function Bi(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function Vi(e, t, n, r, i = 1) {
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
//#region src/avatar-picker.tsx
var Hi = {
	gfriends: "图库",
	history: "用过的"
};
function Ui({ kind: e, id: t, name: n, onPicked: r }) {
	let i = H(null), a = H(null), o = H(null), [s, l] = z(null), [u, d] = z(""), [f, p] = z(""), [m, h] = z(""), [g, _] = z(!1);
	B(() => {
		if (!g || s) return;
		let n = new AbortController();
		return W(`/api/avatar-choices?kind=${e}&id=${t}`, n.signal).then(l).catch((e) => {
			n.signal.aborted || d(U(e));
		}), () => n.abort();
	}, [
		g,
		s,
		e,
		t
	]), B(() => {
		c(a.current);
	}, [g, s]);
	let v = () => {
		_(!0), i.current?.showModal();
	}, y = () => {
		_(!1), i.current?.close();
	}, b = async (e, t) => {
		p(t), d("");
		try {
			await e(), y(), l(null), r();
		} catch (e) {
			d(U(e));
		} finally {
			p("");
		}
	}, x = (n) => b(() => G("/api/avatar-pick", {
		kind: e,
		id: t,
		ref: n.ref
	}), n.ref), S = () => b(() => G("/api/avatar-pick", {
		kind: e,
		id: t,
		url: m.trim()
	}), "url"), C = async (n) => b(async () => {
		let r = await fetch(`/api/avatar-pick?kind=${e}&id=${t}&name=${encodeURIComponent(n.name)}`, {
			method: "POST",
			credentials: "same-origin",
			body: n
		});
		if (!r.ok) {
			let e = await r.json().catch(() => null);
			throw Error(e?.error || `请求失败（${r.status}）`);
		}
	}, "file"), w = s?.choices || [], T = (s?.matched_names || []).filter((e) => e !== n), E = s ? T.length ? `${n}：图库里按「${T.join("」「")}」找到的。` : w.length ? `${n}：换上的那张留在本机，随时能换回来。` : `${n}：图库里没有这个名字，用下面两种方式换。` : "正在找可用的图…", D = !!s && s.index_stale && !w.some((e) => e.source === "gfriends");
	return /* @__PURE__ */ K("div", {
		class: "avatarpick",
		children: [/* @__PURE__ */ K("button", {
			type: "button",
			class: "avatarpick-open",
			onClick: v,
			"aria-haspopup": "dialog",
			"aria-label": `更换${n}的头像`,
			title: "更换头像",
			children: /* @__PURE__ */ K("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true",
				children: /* @__PURE__ */ K("use", { href: "#i-plus" })
			})
		}), /* @__PURE__ */ K("dialog", {
			ref: i,
			class: "geist-modal avatarpick-popover",
			"aria-label": "更换头像",
			onCancel: y,
			onClick: (e) => {
				e.target === i.current && y();
			},
			children: [/* @__PURE__ */ K("div", {
				class: "avatarpick-head",
				children: [
					/* @__PURE__ */ K("span", {
						class: "avatarpick-mark",
						"aria-hidden": "true",
						children: /* @__PURE__ */ K("svg", {
							viewBox: "0 0 24 24",
							children: /* @__PURE__ */ K("use", { href: "#i-user-round" })
						})
					}),
					/* @__PURE__ */ K("div", {
						class: "avatarpick-headtext",
						children: [
							/* @__PURE__ */ K("div", {
								class: "avatarpick-title",
								children: [/* @__PURE__ */ K("h3", { children: "更换头像" }), !!w.length && /* @__PURE__ */ K("span", {
									class: "geist-badge",
									children: [w.length, " 张可选"]
								})]
							}),
							/* @__PURE__ */ K("p", { children: E }),
							D && /* @__PURE__ */ K("p", {
								class: "avatarpick-note",
								children: "图库索引还没取过，只能从用过的图里选。"
							}),
							u && /* @__PURE__ */ K("p", {
								class: "avatarpick-error",
								role: "alert",
								children: u
							})
						]
					}),
					/* @__PURE__ */ K("button", {
						type: "button",
						class: "avatarpick-close",
						onClick: y,
						"aria-label": "关闭",
						children: /* @__PURE__ */ K("svg", {
							viewBox: "0 0 24 24",
							"aria-hidden": "true",
							children: /* @__PURE__ */ K("use", { href: "#i-x" })
						})
					})
				]
			}), /* @__PURE__ */ K("div", {
				class: "avatarpick-panel",
				children: [/* @__PURE__ */ K("div", {
					class: "avatarpick-gridwrap",
					children: /* @__PURE__ */ K("div", {
						class: "avatarpick-grid",
						role: "listbox",
						"aria-label": "候选头像",
						ref: a,
						children: w.map((n) => /* @__PURE__ */ K("button", {
							type: "button",
							role: "option",
							"aria-selected": n.current,
							disabled: !!f,
							class: `avatarpick-cell${n.current ? " current" : ""}`,
							title: `${Hi[n.source] || n.source} · ${n.label}` + (n.width ? ` · ${n.width}×${n.height}` : "") + (n.found_by ? ` · 按「${n.found_by}」找到` : ""),
							onClick: () => x(n),
							children: [
								/* @__PURE__ */ K("img", {
									loading: "lazy",
									alt: "",
									src: `/avatar-choice?kind=${e}&id=${t}&ref=${encodeURIComponent(n.ref)}`
								}),
								/* @__PURE__ */ K("span", { children: n.label }),
								n.current && /* @__PURE__ */ K("b", { children: "在用" })
							]
						}, n.ref))
					})
				}), /* @__PURE__ */ K("div", {
					class: "avatarpick-actions",
					children: [
						/* @__PURE__ */ K("button", {
							type: "button",
							class: "geist-button",
							disabled: !!f,
							onClick: () => o.current?.click(),
							children: "从本机选图片"
						}),
						/* @__PURE__ */ K("input", {
							ref: o,
							type: "file",
							accept: "image/png,image/jpeg",
							hidden: !0,
							onChange: (e) => {
								let t = e.currentTarget.files?.[0];
								e.currentTarget.value = "", t && C(t);
							}
						}),
						/* @__PURE__ */ K("div", {
							class: "avatarpick-url",
							children: [/* @__PURE__ */ K("input", {
								type: "url",
								class: "geist-input",
								value: m,
								placeholder: "https://…",
								"aria-label": "图片地址",
								onInput: (e) => h(e.currentTarget.value)
							}), /* @__PURE__ */ K("button", {
								type: "button",
								class: "geist-button",
								disabled: !m.trim() || !!f,
								onClick: S,
								children: "用这个地址"
							})]
						})
					]
				})]
			})]
		})]
	});
}
function Wi(e, t) {
	Ne(/* @__PURE__ */ K(Ui, { ...t }), e);
}
function Gi(e) {
	Ne(null, e);
}
//#endregion
//#region src/entity-skeleton.ts
function Ki(e, t, n) {
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
var Z = (e = "60%") => `<span class="skeleton" style="width:${e}"></span>`, Q = () => `${Z("80%")}${Z("48%")}`, $ = (e, t) => e.repeat(t), qi = (e, t = "metricstrip") => `<div class="${t}">${e.map((e) => `<div class="tastesummary"><span class="board-stat-label">${e}</span><b class="board-stat-value">${Z("45%")}</b><small class="board-stat-footer">${Z("60%")}</small></div>`).join("")}</div>`, Ji = (e, t = "skeleton-tabs") => `<div class="${t}">${e.map((e) => `<span>${e}</span>`).join("")}</div>`, Yi = (e) => `<section class="board-radial-card"><header><span>${e}</span><b>${Z()}</b></header><div class="board-rings skeleton-rings"><span class="skeleton skeleton-ring"></span></div><div class="skeleton-lines">${Q()}</div></section>`, Xi = (e) => `<section class="insightpanel"><header>${e}</header><div class="insightpanelbody skeleton-lines">${$(Q(), 3)}</div></section>`;
function Zi() {
	return `<div data-skeleton="detail" role="status" aria-label="正在读取作品详情"><div class="sgrid" aria-hidden="true"><div class="vwrap skeleton-detail-media skeleton"></div><aside class="side"><div class="sidecontent skeleton-lines">${Z("85%")}${Z("65%")}${$(Q(), 4)}</div></aside></div></div>`;
}
function Qi(e) {
	let t = "";
	if (e === "/stats") t = `<div class="insightpage statsdashboard"><header class="insighttoolbar">${Z("38%")}</header>${qi([
		"馆藏视频",
		"看过",
		"内容标签",
		"使用空间"
	])}<section class="insightdetail"><div class="insightdetailbody"><div class="board-inventory-charts">${Yi("网盘与本地")}${Yi("媒体库")}</div></div></section>${Xi("内容标签")}</div>`;
	else if (e === "/taste") t = `<div class="tastepage"><header class="tastehead">${Ji(["浏览器记录", "Peach 内部"])}${Z("24%")}</header>${qi([
		"浏览记录",
		"口味维度",
		"浏览候选",
		"私有导出"
	], "tastesummaries")}<section class="tastehero"><div class="insightcopy"><span>浏览器画像</span><div class="skeleton skeleton-radar"></div></div><div class="tastebars skeleton-lines">${$(Q(), 4)}</div></section>${Xi("口味分析")}<div class="board-activity-charts">${Xi("浏览活动")}${Xi("时间分布")}</div>${Xi("标签")}</div>`;
	else if (e === "/follow-manage") t = `<div class="follow followmanage"><div class="fmanageoverview">${[
		"关注作者",
		"启用来源",
		"检查失败",
		"未看更新"
	].map((e) => `<div><span>${e}</span><b>${Z()}</b></div>`).join("")}</div>${Ji([
		"关注列表",
		"添加关注",
		"来源管理"
	], "follow-workspace-switch")}<div class="fmain"><section class="fsec" data-follow-panel="sources"><div class="fsechead"><h3>关注列表</h3>${Z("30%")}</div><div class="board-follow-selection">${Z("45%")}</div><div class="frows fsources" data-layout="default"><div class="board-follow-list">${$(`<article class="fauthor"><div class="fauthorhead">${Z("40%")}</div><div class="skeleton-lines">${$(Q(), 2)}</div></article>`, 4)}</div></div></section></div></div>`;
	else if (e === "/configuration") t = `<div class="configpage">${Ji([
		"通用",
		"媒体",
		"网络与访问",
		"更新与维护"
	])}<section class="configfieldset"><div class="geist-fieldset-content"><h3 class="geist-fieldset-title">开机自启</h3><div class="skeleton-lines">${$(`<div class="skeleton-setting">${Z("35%")}<span class="skeleton skeleton-toggle"></span></div>`, 3)}</div></div><footer class="geist-fieldset-footer">${Z("100px")}</footer></section></div>`;
	else if (e === "/activity") t = `<div class="activitypage">${[
		"正在进行",
		"被挡下的",
		"最近完成"
	].map((e) => `<section class="activitysection"><h3 class="geist-fieldset-title">${e}</h3><div class="activity-runs"><article class="cleanupfieldset activity-run"><div class="geist-fieldset-content skeleton-lines">${Z("35%")}${Q()}</div></article></div></section>`).join("")}</div>`;
	else if (e === "/duplicates") t = `<div class="review"><div class="collection-summary">${Z("38%")}</div><div class="fsechead dupactions"><h3>批量保留</h3>${Z("40%")}</div>${$(`<section class="dupgroup"><div class="duphead">${Z("45%")}</div><div class="duplist">${$(`<div class="duprow"><span class="dupcover skeleton"></span><span class="dupmarks">${Z()}</span><span class="dupname">${Z("90%")}</span>${Z()}${Z()}${Z()}<span class="duppath">${Z("70%")}</span></div>`, 2)}</div></section>`, 2)}</div>`;
	else if (e === "/quality-goals") t = `<div class="quality-workspace"><div class="collection-summary"><strong>待升级</strong>${Z("20%")}</div><div class="qualitylist">${$(`<article class="qualityitem"><span class="qualitycover skeleton"></span><div class="qualitybody skeleton-lines">${Q()}</div><footer class="qualityactions">${Z("80%")}</footer></article>`, 6)}</div></div>`;
	else if (e === "/playlists") t = `<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><div class="playlistcreate skeleton-lines"><span>新播放列表</span>${Z("200px")}</div></header><div class="playlistcards">${$(`<article class="card playlistcard"><div class="mixstack"><div class="pic skeleton"></div></div><div class="mixmeta"><span class="mav skeleton"></span><div class="mixcopy skeleton-lines">${Q()}</div></div></article>`, 6)}</div></section>`;
	else return "";
	return `<div class="board-page-skeleton" data-skeleton="board${e}" role="status" aria-label="正在读取页面"><div aria-hidden="true">${t}</div></div>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var $i = [
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
function ea() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function ta(e, t) {
	let n = new URLSearchParams();
	for (let t of $i) e[t] && n.set(t, e[t]);
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
function na({ kind: e = "catalog", filtered: t = !1, jav: n = !1, configurable: r = !1, online: i = !1 } = {}) {
	let a = r ? "<a class=\"geist-button primary\" href=\"/configuration\">添加内容</a>" : "", o = "<a class=\"geist-button\" href=\"/follow-manage\">添加来源</a>";
	if (t || n) return f("search", n ? "还没有符合条件的 JAV 作品" : "没有符合条件的内容", n ? "已扫描但尚未补充发行资料的视频可在全部内容中查看。" : "清除筛选或搜索条件后查看全部内容。", { actions: "<a class=\"geist-button primary\" href=\"/?loc=&thumb=0\">查看全部内容</a>" });
	if (e !== "catalog") {
		let t = (i ? {
			tags: "标签",
			performers: "作者"
		}[e] : "") || {
			tags: "标签",
			performers: "艺人",
			creators: "创作者",
			studios: "厂牌",
			agencies: "事务所",
			series: "系列"
		}[e] || "资料";
		return f(e === "tags" ? "tags" : "user-round", "还没有" + t, i ? "添加关注来源并获取内容后，这里会显示来源上的" + t + "。" : "添加内容并补充资料后，这里会显示对应信息。", { actions: i ? o : a + o });
	}
	return f("play", "还没有视频", "添加媒体文件夹或关注来源，开始建立你的馆藏。", { actions: a + o });
}
//#endregion
//#region src/sidebar.ts
function ra(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function ia(e, t) {
	return e.dataset.surface?.split("?")[0] === t.split("?")[0] && e.querySelector(".dnav") ? (e.dataset.surface = t, !1) : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function aa(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/resource-sync.ts
var oa = (e = 0) => Number(e).toLocaleString(), sa = {
	local: "本地磁盘",
	115: "115",
	pikpak: "PikPak"
};
function ca(e, t) {
	let n = e.cache || {
		files: 0,
		bytes: 0
	}, r = !!(e.missing || n.files);
	return `<div class="resourcepanel" data-geist-fieldset><div class="resourcesources">${(e.sources || []).map((e) => `<article>
    <div class="resourcesourcetitle"><b>${sa[e.location] || "媒体来源"}</b><span class="${e.online ? "online" : "offline"}">${e.online ? "可访问" : "离线，已跳过"}</span></div>
    <strong>${e.online ? `${oa(e.missing)} 项` : "—"}</strong>
    <small>${e.online ? `找不到文件 · 已检查 ${oa(e.checked)} 项` : `馆藏中有 ${oa(e.total)} 项`}</small>
    ${e.unreadable ? `<small>${oa(e.unreadable)} 项读取失败，已跳过</small>` : ""}</article>`).join("")}</div>
    <div class="resourcecache"><div><span>可清理的缓存</span><b>${oa(n.files)} 个</b><small>${t(n.bytes)}</small></div>
    <div><span>待移入回收站</span><b>${oa(e.missing)} 项</b></div></div>
    ${r ? g(`将把找不到文件的 ${oa(e.missing)} 项馆藏记录移入回收站，并清理 ${oa(n.files)} 个闲置缓存。`, { label: "清理内容" }) : ""}
    <div class="resourceapplyrow geist-fieldset-footer" data-geist-fieldset-footer>${r ? "<button class=\"geist-button primary\" type=\"button\" id=\"resourceApply\">清理失效记录与缓存</button>" : "<p class=\"resourcesyncok\">已检查可访问的来源，没有待清理的记录或缓存。</p>"}</div></div>`;
}
//#endregion
//#region src/jav-artwork.ts
function la(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function ua(e) {
	return {
		javLayout: la(e.javLayout),
		javImage: da(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function da(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function fa(e, t) {
	return e.is_jav && e.code && e.has_cover && (da(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function pa(e, t) {
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
function ma(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (da(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.classList.remove("panel"), e.removeAttribute("style"), e.closest(".pic")?.style.removeProperty("--cover-blur"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var ha = {
	"library-processing": {
		load: vt,
		component: xt
	},
	scraping: {
		load: $r,
		component: ni
	},
	"quality-goals": {
		load: Xr,
		component: Qr
	},
	configuration: {
		load: er,
		component: sr
	},
	activity: {
		load: ri,
		component: gi
	}
}, ga = () => Object.keys(ha), _a = /* @__PURE__ */ new Map();
async function va(e, t, n, r = {}) {
	let i = ha[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	ba(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	_a.set(t, a);
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
			error: U(e)
		};
	}
	if (_a.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		_a.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	Ne(ue(i.component, s), t);
}
var ya = (e) => !!e && _a.has(e);
function ba(e) {
	let t = _a.get(e);
	t && (t.controller.abort(), _a.delete(e), t.painted && Ne(null, e));
}
//#endregion
export { Et as TASTE_GUIDE_KEY, Tn as activityChartsHtml, Qi as boardPageSkeleton, Ie as boundedPreference, na as catalogEmptyHtml, ta as catalogSuggestions, Ri as clampPage, wt as cleanupSkeletonHtml, St as cloudLocations, Ct as cloudPreferenceLocations, Oi as createReviewSelection, yn as creatorSankeyHtml, Zi as detailSkeletonHtml, Ve as distributionChart, ea as emptyCatalogLayout, Ki as entitySkeletonHtml, ht as followJobProgress, ji as groupReviewRows, Si as identityEvidenceHtml, Mt as initBoardControls, ya as islandMounted, ga as islandNames, fa as javImageKind, pt as jobActivityHtml, Be as jobProgressHtml, Bi as matchesFaceSource, Wi as mountAvatarPicker, At as mountBoardStatePreview, va as mountIsland, Re as mountNumberSetting, Vi as nativeImageFit, da as normalizeJavImage, la as normalizeJavLayout, ua as normalizeJavPreferences, Li as pageCount, zi as paginationHtml, pa as panelFrame, Pe as preferredDirection, Ue as radarChart, Sn as radialCardHtml, He as rankedChart, yi as refreshStore, ca as resourceScanHtml, xi as reviewImageHtml, Ei as selectGroup, wi as selectRange, Ti as selectionSummary, ra as sidebarHasCatalogContent, On as sidebarSectionHtml, aa as sidebarTagCounts, ze as statCardBody, vi as storeNames, jt as syncBoardRange, ma as syncJavImages, Le as syncNumberSetting, Di as syncSelectionToolbar, ia as syncSidebarSurface, Tt as tasteHistoryGuideHtml, jn as transitionTheme, Gi as unmountAvatarPicker, ba as unmountIsland, ki as updateReviewSticky, mt as watchJob, En as wireActivityCharts, bn as wireCreatorSankey, Rt as wireExpandableRanks, Lt as wireGrowingCharts, Cn as wireRadialCards, Ci as wireReviewPictures, Fi as wireReviewSelection, kn as wireSidebarGroups, Dt as wireTasteHistoryGuide };
