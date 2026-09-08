import { MEDIA_SOURCE_ICONS as e, checkboxHtml as t, confirmModal as n, emptyStateHtml as r, fieldsetTitle as i, loadingDotsHtml as a, noteHtml as o, progressHtml as s, projectBannerHtml as c, selectFieldHtml as l, selectOptionIconHtml as u, setActionBusy as d, wireCollapse as f, wireSelectField as p } from "/js/ui-components.js";
import { LOC as m, esc as h, faviconUrl as g, fmtDur as _, fmtSize as v, icon as y, requestErrorMessage as b } from "/js/core.js";
//#region node_modules/preact/dist/preact.module.js
var x, S, C, w, T, E, D, O, k, A, j, ee, M, N, P, F = {}, te = [], ne = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, re = Array.isArray;
function I(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function ie(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function ae(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? x.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return oe(e, o, r, i, null);
}
function oe(e, t, n, r, i) {
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
function L(e) {
	return e.children;
}
function se(e, t) {
	this.props = e, this.context = t;
}
function R(e, t) {
	if (t == null) return e.__ ? R(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? R(e) : null;
}
function ce(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = I({}, t);
		a.__v = t.__v + 1, S.vnode && S.vnode(a), ye(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? R(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, xe(r, a, i), t.__e = t.__ = null, a.__e != n && le(a);
	}
}
function le(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), le(e);
}
function ue(e) {
	(!e.__d && (e.__d = !0) && T.push(e) && !de.__r++ || E != S.debounceRendering) && ((E = S.debounceRendering) || D)(de);
}
function de() {
	try {
		for (var e, t = 1; T.length;) T.length > t && T.sort(O), e = T.shift(), t = T.length, ce(e);
	} finally {
		T.length = de.__r = 0;
	}
}
function fe(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || te, v = t.length;
	for (c = pe(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || F, p.__i = d, g = ye(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && we(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = me(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function pe(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = oe(null, o, null, null, null) : re(o) ? o = e.__k[a] = oe(L, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = oe(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = he(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = R(s)), Te(s, s));
	return r;
}
function me(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = me(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = R(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function he(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function ge(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || ne.test(t) ? n : n + "px";
}
function _e(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || ge(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || ge(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(ee, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[j] = r[j] : (n[j] = M, e.addEventListener(t, a ? P : N, a)) : e.removeEventListener(t, a ? P : N, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function ve(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[A] == null) t[A] = M++;
			else if (t[A] < n[j]) return;
			return n(S.event ? S.event(t) : t);
		}
	};
}
function ye(e, t, n, r, i, a, o, s, c, l) {
	var u, d, f, p, m, h, g, _, v, y, b, x, C, w, T, E, D = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (u = S.__b) && u(t);
	n: if (typeof D == "function") {
		d = o.length;
		try {
			if (v = t.props, y = D.prototype && D.prototype.render, b = (u = D.contextType) && r[u.__c], x = u ? b ? b.props.value : u.__ : r, n.__c ? _ = (f = t.__c = n.__c).__ = f.__E : (y ? t.__c = f = new D(v, x) : (t.__c = f = new se(v, x), f.constructor = D, f.render = Ee), b && b.sub(f), f.state || (f.state = {}), f.__n = r, p = f.__d = !0, f.__h = [], f._sb = []), y && f.__s == null && (f.__s = f.state), y && D.getDerivedStateFromProps != null && (f.__s == f.state && (f.__s = I({}, f.__s)), I(f.__s, D.getDerivedStateFromProps(v, f.__s))), m = f.props, h = f.state, f.__v = t, p) y && D.getDerivedStateFromProps == null && f.componentWillMount != null && f.componentWillMount(), y && f.componentDidMount != null && f.__h.push(f.componentDidMount);
			else {
				if (y && D.getDerivedStateFromProps == null && v !== m && f.componentWillReceiveProps != null && f.componentWillReceiveProps(v, x), t.__v == n.__v || !f.__e && f.shouldComponentUpdate != null && !1 === f.shouldComponentUpdate(v, f.__s, x)) {
					t.__v != n.__v && (f.props = v, f.state = f.__s, f.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), te.push.apply(f.__h, f._sb), f._sb = [], f.__h.length && o.push(f), s = R(n);
					break n;
				}
				f.componentWillUpdate != null && f.componentWillUpdate(v, f.__s, x), y && f.componentDidUpdate != null && f.__h.push(function() {
					f.componentDidUpdate(m, h, g);
				});
			}
			if (f.context = x, f.props = v, f.__P = e, f.__e = !1, C = S.__r, w = 0, y) f.state = f.__s, f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), te.push.apply(f.__h, f._sb), f._sb = [];
			else do
				f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), f.state = f.__s;
			while (f.__d && ++w < 25);
			f.state = f.__s, f.getChildContext != null && (r = I(I({}, r), f.getChildContext())), y && !p && f.getSnapshotBeforeUpdate != null && (g = f.getSnapshotBeforeUpdate(m, h)), T = u != null && u.type === L && u.key == null ? Se(u.props.children) : u, s = fe(e, re(T) ? T : [T], t, n, r, i, a, o, s, c, l), f.base = t.__e, t.__u &= -161, f.__h.length && o.push(f), _ && (f.__E = f.__ = null);
		} catch (e) {
			if (o.length = d, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (E = a.length; E--;) ie(a[E]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || be(t), S.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = Ce(n.__e, t, n, r, i, a, o, c, l);
	return (u = S.diffed) && u(t), 128 & t.__u ? void 0 : s;
}
function be(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(be));
}
function xe(e, t, n) {
	for (var r = 0; r < n.length; r++) we(n[r], n[++r], n[++r]);
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
function Se(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : re(e) ? e.map(Se) : e.constructor === void 0 ? I({}, e) : null;
}
function Ce(e, t, n, r, i, a, o, s, c) {
	var l, u, d, f, p, m, h, g = n.props || F, _ = t.props, v = t.type;
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
		for (l in g) p = g[l], l == "dangerouslySetInnerHTML" ? d = p : l == "children" || l in _ || l == "value" && "defaultValue" in _ || l == "checked" && "defaultChecked" in _ || _e(e, l, null, p, i);
		for (l in _) p = _[l], l == "children" ? f = p : l == "dangerouslySetInnerHTML" ? u = p : l == "value" ? m = p : l == "checked" ? h = p : s && typeof p != "function" || g[l] === p || _e(e, l, p, g[l], i);
		if (u) s || d && (u.__html == d.__html || u.__html == e.innerHTML) || (e.innerHTML = u.__html), t.__k = [];
		else if (d && (e.innerHTML = ""), fe(t.type == "template" ? e.content : e, re(f) ? f : [f], t, n, r, v == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && R(n, 0), s, c), a != null) for (l = a.length; l--;) ie(a[l]);
		s && v != "textarea" || (l = "value", v == "progress" && m == null ? e.removeAttribute("value") : m != null && (m !== e[l] || v == "progress" && !m || v == "option" && m != g[l]) && _e(e, l, m, g[l], i), l = "checked", h != null && h != e[l] && _e(e, l, h, g[l], i));
	}
	return e;
}
function we(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		S.__e(e, n);
	}
}
function Te(e, t, n) {
	var r, i;
	if (S.unmount && S.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || we(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			S.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && Te(r[i], t, n || typeof e.type != "function");
	n || ie(e.__e), e.__c = e.__ = e.__e = void 0;
}
function Ee(e, t, n) {
	return this.constructor(e, n);
}
function De(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), S.__ && S.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], ye(t, e = (!r && n || t).__k = ae(L, null, [e]), i || F, F, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? x.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), xe(a, e, o), e.props.children = null;
}
x = te.slice, S = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, C = 0, w = function(e) {
	return e != null && e.constructor === void 0;
}, se.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = I({}, this.state);
	typeof e == "function" && (e = e(I({}, n), this.props)), e && I(n, e), e != null && this.__v && (t && this._sb.push(t), ue(this));
}, se.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), ue(this));
}, se.prototype.render = L, T = [], D = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, O = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, de.__r = 0, k = Math.random().toString(8), A = "__d" + k, j = "__a" + k, ee = /(PointerCapture)$|Capture$/i, M = 0, N = ve(!1), P = ve(!0);
//#endregion
//#region src/sort-preferences.ts
function Oe(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/number-setting.ts
var ke = {
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
function Ae(e, t, n, r) {
	return Number.isInteger(e) && e >= t && e <= n ? e : r;
}
function je(e, t, n) {
	let r = e.querySelector("input[type=number]"), i = e.querySelector("[role=switch]"), a = e.querySelector(".board-number-fields");
	r && (r.disabled = n, t !== null && t > 0 && (r.value = String(t))), i && (i.disabled = n, t !== null && (i.checked = t > 0)), a && t !== null && (a.hidden = t === 0);
}
function Me(e, t, n, r, i) {
	let a = ke[t];
	if (!a) return !1;
	let { min: o, max: s, unit: c, optional: l, fallback: u } = a, d = `peach.number.${t}`, f = Ae(Number(localStorage.getItem(d)), o, s, r > 0 ? r : u), p = document.createElement("div");
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
var z = (e) => String(e ?? "").replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function Ne(e, t, n, r = "chart-no-axes-combined") {
	return `<span class="board-stat-label"><span class="board-stat-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><use href="#i-${/^[a-z0-9-]+$/.test(r) ? r : "database"}"/></svg></span>${z(e)}</span><b class="board-stat-value">${z(t)}</b><small class="board-stat-footer">${z(n || "当前记录")}</small>`;
}
function Pe(e, t, n) {
	if (!Number.isFinite(n) || n <= 0) return "";
	let r = Math.max(0, Math.min(n, Number.isFinite(t) ? t : 0)), i = r / n * 100;
	return `<div class="board-job-progress" role="progressbar" aria-label="${z(e)}" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${r}"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle class="board-job-track" cx="18" cy="18" r="15"/><circle class="board-job-fill" cx="18" cy="18" r="15" pathLength="100" stroke-dasharray="${i} ${100 - i}" transform="rotate(-90 18 18)"/></svg><span>${z(e)}<small>${Math.round(i)}%</small></span></div>`;
}
function Fe(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0), r = n.reduce((e, t) => e + t.score, 0);
	if (!r) return "";
	let i = 0, a = n.map((e, t) => {
		let n = e.score / r * 100, a = `<circle cx="100" cy="100" r="72" pathLength="100" fill="none" stroke="var(--chart-${t % 4})" stroke-width="22" stroke-dasharray="${n} ${100 - n}" stroke-dashoffset="${-i}"><title>${z(e.name)}：${e.score.toLocaleString()}</title></circle>`;
		return i += n, a;
	}).join("");
	return `<svg class="board-distribution" viewBox="0 0 200 200" role="img" aria-label="${z(t)}"><g transform="rotate(-90 100 100)">${a}</g><text x="100" y="100" text-anchor="middle" dominant-baseline="middle">${z(t)}</text></svg>`;
}
function Ie(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0).slice().sort((e, t) => t.score - e.score).slice(0, 8);
	if (!n.length) return "";
	let r = n[0].score, i = n.map((e) => `<li><span class="board-rank-fill" style="width:${(e.score / r * 100).toFixed(2)}%"></span><span>${z(e.name)}</span><b>${e.score.toLocaleString()}</b></li>`).join("");
	return `<ol class="board-ranked-chart" aria-label="${z(t)}">${i}</ol>`;
}
function Le(e, t) {
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
		return `<text x="${n}" y="${r}" text-anchor="${n < 145 ? "end" : n > 175 ? "start" : "middle"}">${z(e.name)}</text>`;
	}).join("");
	return `<svg class="board-radar" viewBox="0 0 320 280" role="img" aria-label="${z(t)}"><title>${z(n.map((e) => `${e.name} ${e.score}`).join("，"))}</title>${s}<polygon points="${o((e) => n[e].score / r * 100)}" class="board-radar-value"/>${c}</svg>`;
}
//#endregion
//#region src/sidebar-groups.ts
var Re = (e) => e.replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function ze(e, t, n = "", r = "") {
	if (!t) return "";
	let i = `sidebar-group-${encodeURIComponent(e)}`;
	return `<details class="sec${r ? " cat-" + Re(r) : ""}" data-sidebar-group="${Re(e)}"><summary role="button" class="board-section-toggle"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${Re(e)}</span>${n}</summary><div class="board-sidebar-body" id="${i}">${t}</div></details>`;
}
function Be(e) {
	e.querySelectorAll("[data-sidebar-group]").forEach((e) => {
		if (e.dataset.sidebarWired) return;
		e.dataset.sidebarWired = "true";
		let t = e.querySelector(".board-section-toggle"), n = e.querySelector(".board-sidebar-body"), r = `peach.sidebar.group.${e.dataset.sidebarGroup}`, i = null;
		try {
			i = sessionStorage.getItem(r);
		} catch {}
		let a = !!n.querySelector("[aria-pressed=true]");
		e.open = i === null ? a || e.classList.contains("cat-src") || e.dataset.sidebarGroup === "时长" : i === "open", t.querySelectorAll("button").forEach((e) => e.addEventListener("click", (e) => e.stopPropagation()));
	}), f(e, "details[data-sidebar-group]", "sidebar-collapse"), e.querySelectorAll(".board-section-toggle").forEach((e) => {
		e.dataset.persistWired || (e.dataset.persistWired = "true", e.addEventListener("click", () => {
			let t = `peach.sidebar.group.${e.closest("[data-sidebar-group]").dataset.sidebarGroup}`;
			try {
				sessionStorage.setItem(t, e.getAttribute("aria-expanded") === "true" ? "open" : "closed");
			} catch {}
		}));
	});
}
var Ve = !1;
async function He(e, t) {
	if (Ve) return;
	if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
		t();
		return;
	}
	let n = e.getBoundingClientRect(), r = n.left + n.width / 2, i = n.top + n.height / 2, a = Math.hypot(Math.max(r, innerWidth - r), Math.max(i, innerHeight - i)) * 2.5, o = document.createElement("style");
	o.textContent = `::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20100%20100%22%3E%3Cdefs%3E%3Cfilter%20id%3D%22b%22%20x%3D%22-50%25%22%20y%3D%22-50%25%22%20width%3D%22200%25%22%20height%3D%22200%25%22%3E%3CfeGaussianBlur%20stdDeviation%3D%222%22%2F%3E%3C%2Ffilter%3E%3C%2Fdefs%3E%3Ccircle%20cx%3D%2250%22%20cy%3D%2250%22%20r%3D%2242%22%20fill%3D%22white%22%20filter%3D%22url(%23b)%22%2F%3E%3C%2Fsvg%3E");mask-repeat:no-repeat;animation:peach-theme-reveal 820ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${r}px ${i}px;mask-size:0px 0px}to{mask-position:${r - a / 2}px ${i - a / 2}px;mask-size:${a}px ${a}px}}`, Ve = !0, document.head.append(o);
	try {
		await document.startViewTransition(t).finished;
	} catch {
		t();
	} finally {
		o.remove(), Ve = !1;
	}
}
//#endregion
//#region src/api.ts
var Ue = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(b(e, t)), this.name = "ApiError", this.status = t, this.body = n;
	}
}, We = (e) => {
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
}, B = (e) => b(e);
async function V(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new Ue(We(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function H(e, t, n = "POST", r) {
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
	if (!i.ok) throw new Ue(We(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var Ge, U, Ke, qe, Je = 0, Ye = [], W = S, Xe = W.__b, Ze = W.__r, Qe = W.diffed, $e = W.__c, et = W.unmount, tt = W.__;
function nt(e, t) {
	W.__h && W.__h(U, e, Je || t), Je = 0;
	var n = U.__H || (U.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function G(e) {
	return Je = 1, rt(dt, e);
}
function rt(e, t, n) {
	var r = nt(Ge++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : dt(void 0, t), function(e) {
		var t = r.__N ? r.__N[0] : r.__[0], n = r.t(t, e);
		t !== n && (r.__N = [n, r.__[1]], r.__c.setState({}));
	}], r.__c = U, !U.__f)) {
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
		U.__f = !0;
		var a = U.shouldComponentUpdate, o = U.componentWillUpdate;
		U.componentWillUpdate = function(e, t, n) {
			if (this.__e) {
				var r = a;
				a = void 0, i(e, t, n), a = r;
			}
			o && o.call(this, e, t, n);
		}, U.shouldComponentUpdate = i;
	}
	return r.__N || r.__;
}
function K(e, t) {
	var n = nt(Ge++, 3);
	!W.__s && ut(n.__H, t) && (n.__ = e, n.u = t, U.__H.__h.push(n));
}
function q(e, t) {
	var n = nt(Ge++, 4);
	!W.__s && ut(n.__H, t) && (n.__ = e, n.u = t, U.__h.push(n));
}
function J(e) {
	return Je = 5, it(function() {
		return { current: e };
	}, []);
}
function it(e, t) {
	var n = nt(Ge++, 7);
	return ut(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function at() {
	for (var e; e = Ye.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(ct), t.__h.some(lt), t.__h = [];
		} catch (n) {
			t.__h = [], W.__e(n, e.__v);
		}
	}
}
W.__b = function(e) {
	U = null, Xe && Xe(e);
}, W.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), tt && tt(e, t);
}, W.__r = function(e) {
	Ze && Ze(e), Ge = 0;
	var t = (U = e.__c).__H;
	t && (Ke === U ? (t.__h = [], U.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(ct), t.__h.some(lt), t.__h = [], Ge = 0)), Ke = U;
}, W.diffed = function(e) {
	Qe && Qe(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Ye.push(t) !== 1 && qe === W.requestAnimationFrame || ((qe = W.requestAnimationFrame) || st)(at)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), Ke = U = null;
}, W.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(ct), e.__h = e.__h.filter(function(e) {
				return !e.__ || lt(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], W.__e(n, e.__v);
		}
	}), $e && $e(e, t);
}, W.unmount = function(e) {
	et && et(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			ct(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && W.__e(t, n.__v));
};
var ot = typeof requestAnimationFrame == "function";
function st(e) {
	var t, n = function() {
		clearTimeout(r), ot && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	ot && (t = requestAnimationFrame(n));
}
function ct(e) {
	var t = U, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), U = t;
}
function lt(e) {
	var t = U;
	e.__c = e.__(), U = t;
}
function ut(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function dt(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var ft = 0;
Array.isArray;
function Y(e, t, n, r, i, a) {
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
		__v: --ft,
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
function pt({ id: e, label: t, value: n, onInput: r, error: i, help: a, current: o = !1, disabled: s = !1 }) {
	return /* @__PURE__ */ Y("div", {
		class: "configfield",
		children: [
			/* @__PURE__ */ Y("label", {
				for: e,
				children: t
			}),
			/* @__PURE__ */ Y("input", {
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
			i || a ? /* @__PURE__ */ Y("p", {
				id: `${e}-hint`,
				class: i ? "configbad" : "confighelp",
				role: i ? "alert" : void 0,
				children: i || a
			}) : null
		]
	});
}
function mt({ initial: e, receipt: t }) {
	let [n, r] = G(e), [a, s] = G(""), [c, l] = G(""), [u, f] = G(""), [p, m] = G(!1), [h, g] = G(""), [_, v] = G({}), y = J(null), b = J(!1), x = J(null);
	return /* @__PURE__ */ Y("form", {
		class: "configfieldset",
		"data-fieldset-type": p ? "warning" : void 0,
		onSubmit: async (e) => {
			if (e.preventDefault(), b.current) return;
			g("");
			let i = {};
			if (n.mode === "password" && !a && (i.current_password = "请输入当前访问密码"), p || ((c.length < 8 || c.length > 256) && (i.password = "访问密码需为 8–256 个字符"), c !== u && (i.confirmation = "两次输入的密码不一致")), v(i), Object.keys(i).length) {
				requestAnimationFrame(() => y.current?.querySelector("[aria-invalid=\"true\"]")?.focus());
				return;
			}
			b.current = !0, d(x.current, !0);
			try {
				let e = await H("/api/configuration/access", {
					revision: n.revision,
					action: p ? "disable" : "set",
					confirm_disable: p,
					current_password: a,
					password: p ? "" : c,
					confirmation: p ? "" : u
				});
				r(e), s(""), l(""), f(""), m(!1), v({}), t(e.mode === "open" ? "已关闭访问密码" : "已保存访问密码");
			} catch (e) {
				let t = e instanceof Ue ? e.body : null, n = t?.errors || t?.detail?.errors;
				n ? v(n) : g(B(e));
			} finally {
				b.current = !1, d(x.current, !1);
			}
		},
		"aria-labelledby": "accessTitle",
		noValidate: !0,
		ref: y,
		children: [/* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ Y("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: i("accessTitle", "访问密码") } }), /* @__PURE__ */ Y("p", {
						class: "confighelp",
						children: n.mode === "open" ? "未设置密码，能连接到 Peach 的设备可直接访问。" : n.mode === "legacy" ? "当前使用系统生成的访问口令。你可以设置自己的密码，或关闭登录要求。" : n.mode === "locked" ? "访问设置无法读取，请在本机检查配置文件。" : "已设置密码。新设备需要登录，保持登录时间在登录页选择。"
					})]
				}),
				n.mode === "password" || n.mode === "legacy" ? /* @__PURE__ */ Y("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ Y("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ Y("input", {
							type: "checkbox",
							checked: p,
							onChange: (e) => m(e.currentTarget.checked)
						}), /* @__PURE__ */ Y("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ Y("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ Y("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ Y("span", { children: "关闭访问密码，允许能连接到 Peach 的设备直接访问" })]
				}) : null,
				n.mode === "password" ? /* @__PURE__ */ Y(pt, {
					id: "access-current",
					label: "当前访问密码",
					value: a,
					onInput: s,
					error: _.current_password,
					current: !0
				}) : null,
				n.mode === "locked" ? null : /* @__PURE__ */ Y(L, { children: [/* @__PURE__ */ Y(pt, {
					id: "access-password",
					label: n.mode === "password" ? "新访问密码" : "设置访问密码",
					value: c,
					onInput: l,
					disabled: p,
					error: p ? void 0 : _.password,
					help: p ? "关闭访问密码时无需填写。" : "至少 8 个字符。保存后其他设备需要重新登录。"
				}), /* @__PURE__ */ Y(pt, {
					id: "access-confirm",
					label: "确认访问密码",
					value: u,
					onInput: f,
					disabled: p,
					error: p ? void 0 : _.confirmation
				})] }),
				p && /* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: o("保存后，能连接到 Peach 的设备将直接访问馆藏。", {
					variant: "warning",
					label: "访问范围"
				}) } }),
				h ? /* @__PURE__ */ Y("p", {
					class: "configbad",
					role: "alert",
					children: h
				}) : null
			]
		}), n.mode === "locked" ? null : /* @__PURE__ */ Y("div", {
			class: "geist-fieldset-footer",
			children: [/* @__PURE__ */ Y("p", { children: "保存后立即生效。" }), /* @__PURE__ */ Y("button", {
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
var ht = /* @__PURE__ */ new Set([
	"downloading",
	"verifying",
	"extracting",
	"preparing",
	"restarting",
	"installing"
]);
function gt({ initial: e, initialJob: t }) {
	let [r, a] = G(e), [c, l] = G(t || {
		state: "idle",
		progress: 0
	}), [u, f] = G(""), p = J(null), m = J(!0), h = J(!1), g = J(null);
	K(() => {
		d(g.current, ht.has(c.state));
	}, [c.state]), K(() => () => {
		m.current = !1, p.current?.abort();
	}, []);
	let _ = async () => {
		let e = await H("/api/configuration/update-restart", {});
		m.current && l(e);
	};
	K(() => {
		c.state !== "ready" || h.current || (h.current = !0, n({
			title: "更新已准备好",
			body: `Peach ${c.version || ""} 将在重启后安装。`,
			confirmLabel: "立即重启",
			cancelLabel: "稍后",
			onConfirm: _
		}));
	}, [c.state]), K(() => {
		if (!ht.has(c.state)) return;
		let e = new AbortController(), t, n = 0, r = async () => {
			try {
				let t = await V("/api/configuration/update-status", e.signal);
				e.signal.aborted || (l(t), n = 0, t.state === "complete" && a((e) => ({
					...e,
					current_version: t.version || e.current_version,
					state: "current",
					message: "已是最新测试版。"
				})));
			} catch {
				++n >= 120 && !e.signal.aborted && f("尚未连接到 Peach，请检查托盘后刷新页面。");
			}
			!e.signal.aborted && n < 120 && (t = setTimeout(r, 1e3));
		};
		return t = setTimeout(r, 1e3), () => {
			e.abort(), clearTimeout(t);
		};
	}, [c.state]);
	let v = async (e) => {
		if (p.current || ht.has(c.state)) return;
		let t = new AbortController();
		p.current = t, h.current = !1, f(""), d(e, !0);
		try {
			let e = await H("/api/configuration/update", {}, "POST", t.signal);
			t.signal.aborted || l(e);
		} catch (e) {
			t.signal.aborted || f(B(e));
		} finally {
			p.current = null, d(e, !1);
		}
	}, y = async (t) => {
		if (p.current) return;
		let n = new AbortController();
		p.current = n, d(t, !0), f("");
		try {
			let e = await V("/api/configuration/updates", n.signal);
			n.signal.aborted || a(e);
		} catch (t) {
			n.signal.aborted || (a({
				...e,
				state: "error"
			}), f(B(t)));
		} finally {
			p.current = null, d(t, !1);
		}
	};
	return /* @__PURE__ */ Y("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configUpdatesTitle",
		children: [/* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: i("configUpdatesTitle", "检查更新") } }),
				/* @__PURE__ */ Y("dl", {
					class: "configfacts",
					children: [
						/* @__PURE__ */ Y("dt", { children: "当前版本" }),
						/* @__PURE__ */ Y("dd", { children: r.current_version }),
						/* @__PURE__ */ Y("dt", { children: "安装方式" }),
						/* @__PURE__ */ Y("dd", { children: r.installation }),
						/* @__PURE__ */ Y("dt", { children: "更新通道" }),
						/* @__PURE__ */ Y("dd", { children: r.channel }),
						/* @__PURE__ */ Y("dt", { children: "最新版本" }),
						/* @__PURE__ */ Y("dd", { children: r.latest_version || (r.state === "unchecked" ? "尚未检查" : "未取得") })
					]
				}),
				r.state === "available" && !u ? /* @__PURE__ */ Y("div", {
					role: "status",
					dangerouslySetInnerHTML: { __html: o(r.message, { label: "有可用更新" }) }
				}) : /* @__PURE__ */ Y("p", {
					class: u || r.state === "error" ? "configbad" : "confighelp",
					role: u || r.state === "error" ? "alert" : "status",
					children: u || r.message
				}),
				c.state === "idle" ? null : /* @__PURE__ */ Y("div", {
					"aria-live": "polite",
					children: [/* @__PURE__ */ Y("p", {
						class: c.state === "error" ? "configbad" : "confighelp",
						children: c.message
					}), c.state === "error" ? null : /* @__PURE__ */ Y(L, { children: [
						/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: s("更新准备进度：下载、校验、解压、准备安装", c.progress, 100, { stops: [
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
						/* @__PURE__ */ Y("p", {
							class: "confighelp",
							children: ["下载 → 校验 → 解压 → 准备安装 · ", c.message]
						}),
						/* @__PURE__ */ Y("p", {
							class: "confighelp",
							children: c.state === "downloading" && c.total ? `${((c.downloaded || 0) / 1048576).toFixed(1)} / ${(c.total / 1048576).toFixed(1)} MB` : `${c.progress}%`
						})
					] })]
				})
			]
		}), /* @__PURE__ */ Y("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [
				/* @__PURE__ */ Y("a", {
					class: "geist-button externallink",
					href: r.release_url,
					target: "_blank",
					rel: "noreferrer",
					children: ["查看发布页", /* @__PURE__ */ Y("svg", {
						class: "externalmark",
						viewBox: "0 0 24 24",
						"aria-hidden": "true",
						children: /* @__PURE__ */ Y("use", { href: "#i-external-link" })
					})]
				}),
				c.state === "ready" ? /* @__PURE__ */ Y("button", {
					type: "button",
					class: "geist-button primary",
					onClick: () => {
						n({
							title: "更新已准备好",
							body: `Peach ${c.version || ""} 将在重启后安装。`,
							confirmLabel: "立即重启",
							cancelLabel: "稍后",
							onConfirm: _
						});
					},
					children: "重启安装"
				}) : null,
				r.state === "available" && r.installation === "独立测试包" && c.state !== "ready" ? /* @__PURE__ */ Y("button", {
					ref: g,
					type: "button",
					class: "geist-button primary",
					onClick: (e) => v(e.currentTarget),
					children: "下载并安装"
				}) : null,
				/* @__PURE__ */ Y("button", {
					type: "button",
					class: "geist-button",
					disabled: ht.has(c.state),
					onClick: (e) => y(e.currentTarget),
					children: "检查更新"
				})
			]
		})]
	});
}
//#endregion
//#region src/islands/peach-proxy.tsx
function _t({ initial: e, receipt: t }) {
	let [n, r] = G(e), [a, o] = G(e.mode), [s, c] = G(""), [u, f] = G(""), m = J(!1), h = J(null), g = J(null), _ = J(new AbortController());
	K(() => () => _.current.abort(), []), q(() => {
		let t = h.current;
		t.innerHTML = l([
			["environment", "系统代理"],
			["direct", "直连"],
			["proxy", "自定义"]
		], e.mode, {
			label: "Peach 代理",
			className: "configselect",
			attr: "data-fixed-width"
		});
		let n = p(t.firstElementChild), r = () => o(n.value);
		return n.addEventListener("change", r), () => {
			n.removeEventListener("change", r), t.replaceChildren();
		};
	}, []);
	async function v() {
		if (!m.current) {
			m.current = !0, d(g.current, !0), f("");
			try {
				let e = await H("/api/configuration/peach-proxy", {
					mode: a,
					proxy: s
				}, "POST", _.current.signal);
				_.current.signal.aborted || (r(e), c(""), t("已保存 Peach 代理"));
			} catch (e) {
				_.current.signal.aborted || f(B(e));
			} finally {
				m.current = !1, d(g.current, !1);
			}
		}
	}
	return /* @__PURE__ */ Y("form", {
		id: "peachProxy",
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), v();
		},
		children: [/* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ Y("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: i("peachProxyTitle", "Peach 代理") } }), /* @__PURE__ */ Y("p", {
						class: "confighelp",
						children: "采集来源选择“Peach 代理”时共用此设置。"
					})]
				}),
				/* @__PURE__ */ Y("div", { ref: h }),
				a === "proxy" && /* @__PURE__ */ Y("div", {
					class: "configfield",
					children: [/* @__PURE__ */ Y("label", {
						htmlFor: "peachProxyAddress",
						children: "代理地址"
					}), /* @__PURE__ */ Y("input", {
						id: "peachProxyAddress",
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: s,
						placeholder: n.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						onInput: (e) => c(e.currentTarget.value)
					})]
				}),
				n.needs_selection && /* @__PURE__ */ Y("p", {
					class: "configbad",
					children: "已有来源的代理地址不同，请选择公共连接方式。"
				}),
				u && /* @__PURE__ */ Y("p", {
					class: "configbad",
					role: "alert",
					children: u
				})
			]
		}), /* @__PURE__ */ Y("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ Y("button", {
				ref: g,
				class: "geist-button primary",
				type: "submit",
				children: "保存代理"
			})
		})]
	});
}
//#endregion
//#region src/islands/desktop-settings.tsx
function vt({ label: e, checked: t, disabled: n, change: r }) {
	return /* @__PURE__ */ Y("label", {
		class: "configcheck",
		children: [/* @__PURE__ */ Y("span", {
			class: "pcheck",
			children: [/* @__PURE__ */ Y("input", {
				type: "checkbox",
				checked: t,
				disabled: n,
				onChange: (e) => r(e.currentTarget.checked)
			}), /* @__PURE__ */ Y("span", {
				"aria-hidden": "true",
				children: /* @__PURE__ */ Y("svg", {
					viewBox: "0 0 24 24",
					children: /* @__PURE__ */ Y("use", { href: "#i-check" })
				})
			})]
		}), /* @__PURE__ */ Y("span", { children: e })]
	});
}
function yt({ label: e, checked: t, disabled: n, change: r }) {
	return /* @__PURE__ */ Y("label", {
		class: "configtoggle",
		children: [/* @__PURE__ */ Y("span", { children: e }), /* @__PURE__ */ Y("input", {
			class: "ptoggle",
			type: "checkbox",
			role: "switch",
			checked: t,
			disabled: n,
			onChange: (e) => r(e.currentTarget.checked)
		})]
	});
}
function bt({ startup: e, receipt: t }) {
	let [n, r] = G(e.enabled), [a, o] = G(e.silent), [s, c] = G(e.desktop), [l, u] = G(""), f = J(!1), p = J(null), m = e.available && !e.desktop_message;
	async function h() {
		if (!f.current) {
			f.current = !0, d(p.current, !0), u("");
			try {
				await H("/api/configuration/startup", {
					enabled: n,
					silent: a,
					desktop: s
				}), t("已保存开机自启");
			} catch (e) {
				u(B(e));
			} finally {
				f.current = !1, d(p.current, !1);
			}
		}
	}
	return /* @__PURE__ */ Y("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), h();
		},
		children: [/* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: i("startupTitle", "开机自启") } }),
				/* @__PURE__ */ Y("div", {
					class: "configoptions",
					role: "group",
					"aria-labelledby": "startupTitle",
					children: [
						/* @__PURE__ */ Y(yt, {
							label: "开机后启动 Peach",
							checked: n,
							disabled: !e.available,
							change: r
						}),
						/* @__PURE__ */ Y("div", {
							class: "configoption",
							children: [/* @__PURE__ */ Y(yt, {
								label: "静默启动",
								checked: a,
								disabled: !e.available || !n,
								change: o
							}), /* @__PURE__ */ Y("p", {
								class: "confighelp",
								children: "静默启动仅显示托盘，开机后启动 Peach 打开时生效。"
							})]
						}),
						/* @__PURE__ */ Y("div", {
							class: "configoption",
							children: [/* @__PURE__ */ Y(yt, {
								label: "在桌面创建快捷方式",
								checked: s,
								disabled: !m,
								change: c
							}), /* @__PURE__ */ Y("p", {
								class: "confighelp",
								children: e.desktop_message || "双击图标打开 Peach 网页；卸载时一并移除。"
							})]
						})
					]
				}),
				e.message && /* @__PURE__ */ Y("p", {
					class: "confighelp",
					children: e.message
				}),
				l && /* @__PURE__ */ Y("p", {
					class: "configbad",
					role: "alert",
					children: l
				})
			]
		}), /* @__PURE__ */ Y("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ Y("button", {
				ref: p,
				type: "submit",
				class: "geist-button primary",
				disabled: !e.available,
				children: "保存配置"
			})
		})]
	});
}
function xt({ data: e }) {
	let t = J(null);
	return q(() => {
		let n = t.current, r = document.createElement("details");
		r.className = "configdirectories";
		let i = document.createElement("summary");
		i.innerHTML = y("chevron-right") + "<span>数据目录</span>", r.append(i);
		for (let t of [.../* @__PURE__ */ new Set([e.data_root, ...e.directories])]) {
			let e = document.createElement("p");
			e.className = "confighelp", e.textContent = t, r.append(e);
		}
		return n.replaceChildren(r), f(n, "details", "uninstall-data"), () => n.replaceChildren();
	}, [e]), /* @__PURE__ */ Y("div", { ref: t });
}
function St({ uninstall: e }) {
	let [t, r] = G(!1), [a, o] = G("");
	async function s() {
		await n({
			title: "卸载 Peach",
			danger: !0,
			body: t ? "将退出 Peach，移除程序、开机自启、桌面图标、设置、本地数据库、观看记录、凭据和缓存。原始媒体文件保留。" : "将退出 Peach 并移除程序、开机自启和桌面图标。设置、本地数据库、观看记录与缓存保留。",
			confirmLabel: "卸载 Peach",
			onConfirm: async () => {
				let e = await H("/api/configuration/uninstall", {
					delete_data: t,
					confirmation: "卸载 Peach"
				});
				o(e.message);
			}
		});
	}
	return /* @__PURE__ */ Y("section", {
		id: "uninstallPeach",
		class: "configfieldset configdanger",
		"data-geist-fieldset": !0,
		"data-fieldset-type": "error",
		children: [/* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ Y("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: i("uninstallTitle", "卸载 Peach") } }), e.available && /* @__PURE__ */ Y("p", {
						class: "confighelp",
						children: "卸载会退出 Peach、移除程序、开机自启和桌面图标。原始媒体文件保留。"
					})]
				}),
				/* @__PURE__ */ Y(vt, {
					label: "完全卸载：同时删除设置、本地数据库、观看记录、凭据和缓存",
					checked: t,
					disabled: !e.full_available || !!a,
					change: r
				}),
				/* @__PURE__ */ Y(xt, { data: e }),
				e.message && /* @__PURE__ */ Y("p", {
					class: "confighelp",
					children: e.message
				}),
				a && /* @__PURE__ */ Y("p", {
					class: "confighelp",
					role: "status",
					children: a
				})
			]
		}), /* @__PURE__ */ Y("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ Y("button", {
				type: "button",
				class: "geist-button danger",
				disabled: !e.available || !!a,
				onClick: () => void s(),
				children: "卸载 Peach"
			})
		})]
	});
}
//#endregion
//#region src/islands/clouddrive-guide.tsx
var Ct = [
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
function wt() {
	let e = J(null);
	return q(() => {
		e.current && f(e.current, "details", "clouddrive-guide");
	}, []), /* @__PURE__ */ Y("div", {
		ref: e,
		class: "cloudguide",
		children: [/* @__PURE__ */ Y("p", {
			class: "confighelp",
			children: ["先在 CloudDrive 登录网盘并挂载，开启「启动时自动挂载」。", /* @__PURE__ */ Y("a", {
				class: "externallink",
				href: "https://www.clouddrive2.com/help.html",
				target: "_blank",
				rel: "noreferrer",
				children: ["挂载帮助", /* @__PURE__ */ Y("svg", {
					class: "externalmark",
					viewBox: "0 0 24 24",
					"aria-hidden": "true",
					children: /* @__PURE__ */ Y("use", { href: "#i-external-link" })
				})]
			})]
		}), /* @__PURE__ */ Y("details", { children: [
			/* @__PURE__ */ Y("summary", { children: [/* @__PURE__ */ Y("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true",
				children: /* @__PURE__ */ Y("use", { href: "#i-chevron-right" })
			}), "CloudDrive 速度与缓存建议"] }),
			/* @__PURE__ */ Y("p", {
				class: "confighelp",
				children: "看缓存放在哪块硬盘上，照那一行填。表里是起步值，先保证播放不卡，再拿同一个视频比较打开速度、拖动和流量；填得越大不一定越快。"
			}),
			/* @__PURE__ */ Y("div", {
				class: "cloudguide-tablewrap",
				children: /* @__PURE__ */ Y("table", {
					class: "cloudguide-table",
					children: [/* @__PURE__ */ Y("thead", { children: /* @__PURE__ */ Y("tr", { children: [
						/* @__PURE__ */ Y("th", {
							scope: "col",
							children: "缓存所在硬盘"
						}),
						/* @__PURE__ */ Y("th", {
							scope: "col",
							children: "缓存上限"
						}),
						/* @__PURE__ */ Y("th", {
							scope: "col",
							children: "读取长度（默认 / 最小）"
						}),
						/* @__PURE__ */ Y("th", {
							scope: "col",
							children: "同时处理视频"
						})
					] }) }), /* @__PURE__ */ Y("tbody", { children: Ct.map((e) => /* @__PURE__ */ Y("tr", { children: [
						/* @__PURE__ */ Y("th", {
							scope: "row",
							children: e.name
						}),
						/* @__PURE__ */ Y("td", { children: e.cache }),
						/* @__PURE__ */ Y("td", { children: e.read }),
						/* @__PURE__ */ Y("td", { children: e.task })
					] }, e.name)) })]
				})
			}),
			/* @__PURE__ */ Y("ul", {
				class: "cloudguide-notes",
				children: [
					/* @__PURE__ */ Y("li", { children: "缓存上限和清理方式填在 CloudDrive「设置」里，清理方式选 LRU。上限不要填 0，系统盘至少留 40 GiB。" }),
					/* @__PURE__ */ Y("li", { children: "读取长度和下载线程填在每个网盘各自的下载设置里，线程都从 2 开始。看高码率视频还是缓冲就试 512 / 256 KB，打开速度、拖动和流量都没改善就调回去。" }),
					/* @__PURE__ */ Y("li", { children: "Buffer Cache 占内存，磁盘缓存和文件夹缓存占硬盘，三处是分开的设置，改一个管不住另外两个。" }),
					/* @__PURE__ */ Y("li", { children: "填完重新打开 CloudDrive 的设置页确认存住了，再看硬盘实际少了多少。播放期间先暂停批量抽帧、关掉不用的播放页。" })
				]
			}),
			/* @__PURE__ */ Y("p", {
				class: "confighelp",
				children: [
					"三处缓存分别管什么、码率和速度怎么换算、线程上限与直链代理怎么取舍，以及这些起步值的来源，都在",
					/* @__PURE__ */ Y("a", {
						class: "externallink",
						href: "https://github.com/longmeidao/peach/blob/master/docs/CLOUDDRIVE.md",
						target: "_blank",
						rel: "noreferrer",
						children: ["CloudDrive 配置与调优", /* @__PURE__ */ Y("svg", {
							class: "externalmark",
							viewBox: "0 0 24 24",
							"aria-hidden": "true",
							children: /* @__PURE__ */ Y("use", { href: "#i-external-link" })
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
var Tt = "/api/configuration", Et = "/api/pick-folder", Dt = 8e3, Ot = (e, t) => V(Tt, t), kt = ({ html: e, class: t }) => /* @__PURE__ */ Y("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), At = (e) => !(e instanceof Ue) || e.status !== 400 ? null : e.body?.errors ?? null;
function jt({ facts: e }) {
	return /* @__PURE__ */ Y("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ Y(kt, { html: i("configFactsTitle", "运行信息") }), /* @__PURE__ */ Y("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ Y(L, { children: [/* @__PURE__ */ Y("dt", { children: e.term }), /* @__PURE__ */ Y("dd", { children: [e.value, e.download_url ? /* @__PURE__ */ Y("span", {
					class: "confighelp",
					children: [" ", /* @__PURE__ */ Y("a", {
						class: "externallink",
						href: e.download_url,
						target: "_blank",
						rel: "noreferrer",
						children: [e.download_label, /* @__PURE__ */ Y("svg", {
							class: "externalmark",
							viewBox: "0 0 24 24",
							"aria-hidden": "true",
							children: /* @__PURE__ */ Y("use", { href: "#i-external-link" })
						})]
					})]
				}) : null] })] }))
			})]
		})
	});
}
function Mt({ data: t }) {
	let [n, r] = G(t.media_sources), [a, o] = G(""), s = J(null);
	K(() => () => s.current?.abort(), []);
	let c = async (e) => {
		if (s.current) return;
		let t = new AbortController();
		s.current = t, d(e, !0), o("");
		try {
			let e = await V(Tt, t.signal);
			t.signal.aborted || r(e.media_sources);
		} catch (e) {
			t.signal.aborted || o(B(e));
		} finally {
			s.current = null, d(e, !1);
		}
	};
	return n ? /* @__PURE__ */ Y("section", {
		class: "configfieldset",
		"aria-labelledby": "configMountsTitle",
		children: [/* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ Y(kt, { html: i("configMountsTitle", "挂载状态") }),
				/* @__PURE__ */ Y("dl", {
					class: "configfacts",
					children: n.map((t) => /* @__PURE__ */ Y(L, { children: [/* @__PURE__ */ Y("dt", { children: [/* @__PURE__ */ Y("span", {
						"aria-hidden": "true",
						dangerouslySetInnerHTML: { __html: u(e[t.location]) }
					}), {
						local: "本地磁盘",
						115: "CloudDrive · 115",
						pikpak: "CloudDrive · PikPak"
					}[t.location] || t.location] }), /* @__PURE__ */ Y("dd", { children: [
						t.path || "未配置挂载点",
						" ",
						/* @__PURE__ */ Y("span", {
							class: `configstatus ${t.online === !0 ? "online" : t.online === !1 ? "offline" : "unknown"}`,
							children: t.online === !0 ? "在线" : t.online === !1 ? "离线" : "未检测"
						})
					] })] }))
				}),
				a ? /* @__PURE__ */ Y("p", {
					class: "configbad",
					role: "alert",
					children: a
				}) : null
			]
		}), /* @__PURE__ */ Y("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ Y("button", {
				type: "button",
				class: "geist-button",
				onClick: (e) => c(e.currentTarget),
				children: "刷新挂载状态"
			})
		})]
	}) : null;
}
function Nt({ value: t, label: n, onChange: r, libraryIcon: i = !1 }) {
	let a = J(null), o = J(null), s = J(r);
	return s.current = r, q(() => {
		let r = a.current;
		r.innerHTML = l((i ? [
			["", "自动识别"],
			["hard-drive", "磁盘"],
			["database", "资料库"],
			["heart", "心形"],
			["star", "星标"],
			["tags", "标签"],
			["115", "115"],
			["pikpak", "PikPak"]
		] : [
			["local", "本地磁盘"],
			["115", "CloudDrive · 115"],
			["pikpak", "CloudDrive · PikPak"]
		]).map(([t, n]) => [
			t,
			n,
			e[t] || t || "database"
		]), t, { label: n });
		let c = p(r.firstElementChild);
		o.current = c;
		let u = () => s.current(c.value);
		return c.addEventListener("change", u), () => {
			o.current = null, c.disabled = !0, c.removeEventListener("change", u), r.replaceChildren();
		};
	}, [n, i]), q(() => {
		o.current && (o.current.value = t);
	}, [t]), /* @__PURE__ */ Y("div", {
		ref: a,
		class: "configsourcecontrol"
	});
}
function Pt({ data: e, receipt: t }) {
	let n = e.media_sources?.filter((e) => [
		"local",
		"115",
		"pikpak"
	].includes(e.location)), [r, a] = G(n?.length ? n.map((e) => e.path) : e.media_dirs.length ? e.media_dirs : [""]), [s, c] = G(n?.map((e) => e.location) ?? []), [l, u] = G(n?.map((e) => e.root) ?? []), [f, p] = G(n?.map((e) => e.library || "") ?? []), [m, h] = G(n?.map((e) => e.library_icon || "") ?? []), [g, _] = G(String(e.port)), [v, y] = G(!1), [b, x] = G([]), [S, C] = G(""), [w, T] = G(""), [E, D] = G(null), [O, k] = G(null), A = J(!1), j = J(e.revision), ee = J([]), M = J(null);
	q(() => {
		O !== null && (ee.current[O]?.focus(), k(null));
	}, [O]), K(() => {
		if (!E) return;
		let e = setTimeout(() => location.assign(E.url), Dt);
		return () => clearTimeout(e);
	}, [E]);
	let N = (e, t) => {
		a((n) => n.map((n, r) => r === e ? t : n));
	}, P = () => {
		k(r.length), a((e) => [...e, ""]);
	}, F = (e) => {
		c((t) => t.filter((t, n) => n !== e)), u((t) => t.filter((t, n) => n !== e)), p((t) => t.filter((t, n) => n !== e)), h((t) => t.filter((t, n) => n !== e)), a((t) => t.filter((t, n) => n !== e)), x((t) => t.filter((t, n) => n !== e));
	}, te = (e, t) => {
		x((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, ne = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			d(t, !0);
			try {
				let { path: t } = await H(Et, { initial: r[e] ?? "" });
				t && (N(e, t), te(e, ""));
			} catch (t) {
				te(e, B(t));
			} finally {
				d(t, !1);
			}
		}
	};
	return E ? /* @__PURE__ */ Y("div", {
		class: "configsaved",
		role: "status",
		children: /* @__PURE__ */ Y("div", {
			class: "geist-note geist-note-success",
			role: "note",
			children: [/* @__PURE__ */ Y("svg", {
				"aria-hidden": "true",
				viewBox: "0 0 24 24",
				children: /* @__PURE__ */ Y("use", { href: "#i-check" })
			}), /* @__PURE__ */ Y("p", { children: /* @__PURE__ */ Y("span", { children: [
				"配置已保存，Peach 正在重新启动。稍后自动跳转，或点击",
				/* @__PURE__ */ Y("a", {
					href: E.url,
					children: "进入馆藏"
				}),
				"。"
			] }) })]
		})
	}) : /* @__PURE__ */ Y("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configTitle",
		onSubmit: async (n) => {
			if (n.preventDefault(), !A.current) {
				A.current = !0, d(M.current, !0), T("");
				try {
					let n = await H(Tt, {
						revision: j.current,
						media_dirs: r,
						...e.media_sources ? { media_sources: r.map((e, t) => ({
							path: e,
							location: s[t] || "local",
							root: l[t] || "",
							library: f[t] || "",
							library_icon: m[t] || ""
						})) } : {},
						port: g,
						scan_now: v
					});
					j.current = n.revision, x([]), C(""), t("已保存配置"), D(n);
				} catch (e) {
					let t = At(e);
					t ? (x(t.media_dirs ?? []), C(t.port ?? "")) : (x([]), C(""), T(B(e)));
				} finally {
					A.current = !1, d(M.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ Y(kt, { html: i("configTitle", "这台电脑") }),
				/* @__PURE__ */ Y("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ Y("span", {
							class: "configlabel",
							id: "configDirsLabel",
							children: "媒体文件夹"
						}),
						/* @__PURE__ */ Y("div", {
							class: "configdirs",
							role: "group",
							"aria-labelledby": "configDirsLabel",
							children: r.map((t, n) => /* @__PURE__ */ Y("div", {
								class: "configdir",
								children: [
									/* @__PURE__ */ Y("span", {
										class: "configpathlabel",
										children: ["本机文件夹 ", n + 1]
									}),
									/* @__PURE__ */ Y("input", {
										class: "geist-input",
										type: "text",
										value: t,
										"aria-label": `媒体文件夹 ${n + 1}`,
										"aria-invalid": b[n] ? "true" : void 0,
										onInput: (e) => N(n, e.currentTarget.value),
										ref: (e) => {
											ee.current[n] = e;
										}
									}),
									/* @__PURE__ */ Y("button", {
										type: "button",
										class: "geist-button configpick",
										"aria-label": "选择文件夹",
										onClick: (e) => ne(n, e.currentTarget),
										children: /* @__PURE__ */ Y("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ Y("use", { href: "#i-folder-search" })
										})
									}),
									r.length > 1 ? /* @__PURE__ */ Y("button", {
										type: "button",
										class: "geist-button configrm danger",
										"aria-label": "移除这个文件夹",
										onClick: () => F(n),
										children: /* @__PURE__ */ Y("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ Y("use", { href: "#i-x" })
										})
									}) : null,
									/* @__PURE__ */ Y("div", {
										class: "configsource",
										children: [
											/* @__PURE__ */ Y("label", { children: ["媒体库", /* @__PURE__ */ Y("input", {
												class: "geist-input",
												"aria-label": `媒体库 ${n + 1}`,
												maxLength: 80,
												value: f[n] || "",
												placeholder: "同名文件夹归入同一个媒体库",
												onInput: (e) => {
													let t = [...f];
													t[n] = e.currentTarget.value, p(t);
												}
											})] }),
											/* @__PURE__ */ Y("div", {
												class: "configsourcelabel",
												children: ["媒体库图标", /* @__PURE__ */ Y(Nt, {
													libraryIcon: !0,
													label: `媒体库图标 ${n + 1}`,
													value: m[n] || "",
													onChange: (e) => {
														let t = [...m];
														t[n] = e, h(t);
													}
												})]
											}),
											/* @__PURE__ */ Y("div", {
												class: "configsourcelabel",
												children: ["媒体来源", /* @__PURE__ */ Y(Nt, {
													label: `媒体来源 ${n + 1}`,
													value: s[n] || "local",
													onChange: (e) => {
														let t = [...s];
														t[n] = e, c(t);
													}
												})]
											}),
											e.windows === !1 ? /* @__PURE__ */ Y("label", { children: ["Windows 中的对应路径", /* @__PURE__ */ Y("input", {
												class: "geist-input",
												"aria-label": `Windows 中的对应路径 ${n + 1}`,
												value: l[n] || "",
												placeholder: "例如 B:\\\\",
												onInput: (e) => {
													let t = [...l];
													t[n] = e.currentTarget.value, u(t);
												}
											})] }) : null
										]
									}),
									b[n] ? /* @__PURE__ */ Y("p", {
										class: "configbad",
										role: "alert",
										children: b[n]
									}) : null
								]
							}, n))
						}),
						/* @__PURE__ */ Y("button", {
							type: "button",
							class: "geist-button configadd",
							onClick: P,
							children: "添加文件夹"
						}),
						s.some((e) => e === "115" || e === "pikpak") ? /* @__PURE__ */ Y(wt, {}) : null,
						s.some((e) => e === "115" || e === "pikpak") ? e.mount_dependencies?.filter((e) => !e.available).map((e) => /* @__PURE__ */ Y("p", {
							class: "confighelp",
							children: [
								"未检测到 ",
								e.name,
								"。",
								/* @__PURE__ */ Y("a", {
									class: "externallink",
									href: e.download_url,
									target: "_blank",
									rel: "noreferrer",
									children: [
										"下载 ",
										e.name,
										/* @__PURE__ */ Y("svg", {
											class: "externalmark",
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ Y("use", { href: "#i-external-link" })
										})
									]
								})
							]
						})) : null,
						e.windows === !1 ? /* @__PURE__ */ Y("p", {
							class: "confighelp",
							children: "本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\\ 对应本机挂载文件夹。"
						}) : null
					]
				}),
				e.port_editable === !1 ? null : /* @__PURE__ */ Y("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ Y("label", {
							for: "configPort",
							children: "本机访问端口"
						}),
						/* @__PURE__ */ Y("input", {
							id: "configPort",
							class: "geist-input",
							type: "text",
							inputMode: "numeric",
							value: g,
							"aria-invalid": S ? "true" : void 0,
							onInput: (e) => _(e.currentTarget.value)
						}),
						S ? /* @__PURE__ */ Y("p", {
							class: "configbad",
							role: "alert",
							children: S
						}) : null,
						/* @__PURE__ */ Y("p", {
							class: "confighelp",
							children: "浏览器地址里冒号后面的数字，一般不用改。"
						})
					]
				}),
				/* @__PURE__ */ Y("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ Y("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ Y("input", {
							type: "checkbox",
							checked: v,
							onChange: (e) => y(e.currentTarget.checked)
						}), /* @__PURE__ */ Y("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ Y("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ Y("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ Y("span", { children: "保存后扫描并补全资料" })]
				}),
				w ? /* @__PURE__ */ Y(kt, { html: o(w, {
					variant: "error",
					label: "没有保存"
				}) }) : null
			]
		}), /* @__PURE__ */ Y("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [/* @__PURE__ */ Y("p", { children: e.port_editable === !1 ? "保存后 Peach 会重新载入配置。" : "保存后 Peach 会重新启动，端口改了就用新地址打开。" }), /* @__PURE__ */ Y("button", {
				type: "submit",
				class: "geist-button primary",
				ref: M,
				children: "保存配置"
			})]
		})]
	});
}
function Ft({ receipt: e, data: t, error: n }) {
	return n || !t ? /* @__PURE__ */ Y(kt, {
		class: "configpage",
		html: o(n || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		})
	}) : /* @__PURE__ */ Y("div", {
		class: "configpage",
		children: [
			t.startup ? /* @__PURE__ */ Y("h2", {
				class: "configgroup",
				children: "通用"
			}) : null,
			t.startup ? /* @__PURE__ */ Y(bt, {
				startup: t.startup,
				receipt: e
			}) : null,
			/* @__PURE__ */ Y("h2", {
				class: "configgroup",
				children: "媒体"
			}),
			t.editable ? /* @__PURE__ */ Y(Pt, {
				data: t,
				receipt: e
			}) : /* @__PURE__ */ Y(kt, { html: o(t.notice, {
				variant: "secondary",
				label: "只读"
			}) }),
			/* @__PURE__ */ Y(Mt, { data: t }),
			t.peach_proxy || t.access ? /* @__PURE__ */ Y("h2", {
				class: "configgroup",
				children: "网络与访问"
			}) : null,
			t.peach_proxy ? /* @__PURE__ */ Y(_t, {
				initial: t.peach_proxy,
				receipt: e
			}) : null,
			t.access ? /* @__PURE__ */ Y(mt, {
				initial: t.access,
				receipt: e
			}) : null,
			/* @__PURE__ */ Y("h2", {
				class: "configgroup",
				children: "更新与维护"
			}),
			t.updates ? /* @__PURE__ */ Y(gt, {
				initial: t.updates,
				initialJob: t.update_job
			}) : null,
			/* @__PURE__ */ Y(jt, { facts: t.facts }),
			t.uninstall ? /* @__PURE__ */ Y(St, { uninstall: t.uninstall }) : null
		]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var It = Symbol.for("preact-signals");
function Lt() {
	if (Z > 1) Z--;
	else {
		var e, t = !1;
		for ((function() {
			var e = Gt;
			for (Gt = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); Vt !== void 0;) {
			var n = Vt;
			for (Vt = void 0, Ht++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && Yt(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (Ht = 0, Z--, t) throw e;
	}
}
function Rt(e) {
	if (Z > 0) return e();
	Wt = ++Ut, Z++;
	try {
		return e();
	} finally {
		Lt();
	}
}
var zt, X = void 0;
function Bt(e) {
	var t = X, n = zt;
	X = void 0, zt = void 0;
	try {
		return e();
	} finally {
		X = t, zt = n;
	}
}
var Vt = void 0, Z = 0, Ht = 0, Ut = 0, Wt = 0, Gt = void 0, Kt = 0;
function qt(e) {
	if (X !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== X) return t = {
			i: 0,
			S: e,
			p: X.s,
			n: void 0,
			t: X,
			e: void 0,
			x: void 0,
			r: t
		}, X.s !== void 0 && (X.s.n = t), X.s = t, e.n = t, 32 & X.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = X.s, t.n = void 0, X.s.n = t, X.s = t), t;
	}
}
function Q(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
Q.prototype.brand = It, Q.prototype.h = function() {
	return !0;
}, Q.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? Bt(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, Q.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && Bt(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, Q.prototype.subscribe = function(e) {
	var t = this;
	return an(function() {
		var n = t.value;
		Bt(function() {
			return e(n);
		});
	}, { name: "sub" });
}, Q.prototype.valueOf = function() {
	return this.value;
}, Q.prototype.toString = function() {
	return this.value + "";
}, Q.prototype.toJSON = function() {
	return this.value;
}, Q.prototype.peek = function() {
	var e = this;
	return Bt(function() {
		return e.value;
	});
}, Object.defineProperty(Q.prototype, "value", {
	get: function() {
		var e = qt(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (Ht > 100) throw Error("Cycle detected");
			(function(e) {
				Z !== 0 && Ht === 0 && e.l !== Wt && (e.l = Wt, Gt = {
					S: e,
					v: e.v,
					i: e.i,
					o: Gt
				});
			})(this), this.v = e, this.i++, Kt++, Z++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				Lt();
			}
		}
	}
});
function Jt(e, t) {
	return new Q(e, t);
}
function Yt(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function Xt(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function Zt(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function Qt(e, t) {
	Q.call(this, void 0, t), this.x = e, this.s = void 0, this.g = Kt - 1, this.f = 4;
}
Qt.prototype = new Q(), Qt.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === Kt)) return !0;
	if (this.g = Kt, this.f |= 1, this.i > 0 && !Yt(this)) return this.f &= -2, !0;
	var e = X;
	try {
		Xt(this), X = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return X = e, Zt(this), this.f &= -2, !0;
}, Qt.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	Q.prototype.S.call(this, e);
}, Qt.prototype.U = function(e) {
	if (this.t !== void 0 && (Q.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, Qt.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(Qt.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = qt(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function $t(e, t) {
	return new Qt(e, t);
}
function en(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		Z++;
		var n = X;
		X = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, tn(e), t;
		} finally {
			X = n, Lt();
		}
	}
}
function tn(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, en(e);
}
function nn(e) {
	if (X !== this) throw Error("Out-of-order effect");
	Zt(this), X = e, this.f &= -2, 8 & this.f && tn(this), Lt();
}
function rn(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, zt && zt.push(this);
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
	this.f |= 1, this.f &= -9, en(this), Xt(this), Z++;
	var e = X;
	return X = this, nn.bind(this, e);
}, rn.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = Vt, Vt = this);
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
	var i = it(function() {
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
fn.displayName = "ReactiveTextNode", Object.defineProperties(Q.prototype, {
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
			a instanceof Q && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), un("__r", function(e, t) {
	if (e(t), t.type !== L) {
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
	var i = t in e && e.ownerSVGElement === void 0, a = Jt(n);
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
}), se.prototype.shouldComponentUpdate = function(e, t) {
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
	return it(function() {
		return Jt(e, t);
	}, []);
}
var hn = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function gn() {
	Rt(function() {
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
}, bn = Jt(yn), xn = 0, Sn = $t(() => bn.value);
$t(() => bn.value.data?.total ?? null);
function Cn() {
	xn += 1, bn.value = yn;
}
async function wn(e) {
	let t = xn += 1;
	try {
		let n = await V(vn, e);
		return t === xn && (bn.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === xn && (bn.value = {
			data: null,
			error: B(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var Tn = (e, t) => wn(t), En = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function Dn({ openItem: e, javTitleHtml: t, javDisplayName: n, srcBadge: i }) {
	let { data: a, error: s } = Sn.value;
	if (s) return /* @__PURE__ */ Y("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: o(s, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let c = a?.items ?? [];
	return c.length ? /* @__PURE__ */ Y("div", {
		class: "qualitylist",
		children: c.map((r) => /* @__PURE__ */ Y("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ Y("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${n(r)}`,
				onClick: () => e(r.id),
				children: /* @__PURE__ */ Y("img", {
					src: En(r),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ Y("div", { children: [
				/* @__PURE__ */ Y("h3", { children: /* @__PURE__ */ Y("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => e(r.id),
					dangerouslySetInnerHTML: { __html: t(r) }
				}) }),
				/* @__PURE__ */ Y("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ Y("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: i(r.location, r.cost) }
						}),
						/* @__PURE__ */ Y("span", { children: m[r.location] ?? r.location }),
						/* @__PURE__ */ Y("span", { children: _(r.duration) }),
						/* @__PURE__ */ Y("span", { children: v(r.size ?? 0) })
					]
				}),
				r.reason ? /* @__PURE__ */ Y("p", { children: r.reason }) : null
			] })]
		}, r.id))
	}) : /* @__PURE__ */ Y("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: r("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
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
var An = (e, t) => V("/api/scraping", t);
function jn({ value: e, onChange: t }) {
	let n = J(null), r = J(t);
	return r.current = t, q(() => {
		let t = n.current;
		t.innerHTML = l([["peach", "Peach 代理"], ["direct", "直接连接"]], e, { label: "连接方式" });
		let i = p(t.firstElementChild), a = () => r.current(i.value);
		return i.addEventListener("change", a), () => {
			i.disabled = !0, i.removeEventListener("change", a), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ Y("div", {
		ref: n,
		class: "scraping-network"
	});
}
function Mn({ source: e, toast: t }) {
	let [n, r] = G(e), [a, s] = G(e.network), [c, l] = G(""), [u, f] = G(""), [p, m] = G("paste"), [h, _] = G(""), [v, y] = G(!1), [b, x] = G(""), [S, C] = G([]), w = J(null), T = J(null);
	q(() => {
		T.current?.querySelectorAll("footer button").forEach((e) => d(e, v));
	}, [v]);
	let E = J(new AbortController());
	K(() => () => E.current.abort(), []);
	async function D(n) {
		if (!v) {
			y(!0), x(""), C([]);
			try {
				if (n === "check") {
					let t = await H("/api/scraping/check", { source: e.source }, "POST", E.current.signal);
					E.current.signal.aborted || C(t.results);
				} else {
					let i = await H("/api/scraping/settings", {
						source: e.source,
						network: a,
						cookie: c,
						cookies_text: u,
						revoke: n === "revoke"
					}, "POST", E.current.signal);
					E.current.signal.aborted || (r(i.saved), l(""), f(""), _(""), w.current && (w.current.value = ""), t(n === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				E.current.signal.aborted || x(B(e));
			} finally {
				E.current.signal.aborted || y(!1);
			}
		}
	}
	return /* @__PURE__ */ Y("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ Y("form", {
			ref: T,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), D("save");
			},
			children: [/* @__PURE__ */ Y("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ Y("div", {
						class: "geist-fieldset-heading",
						children: [/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: i(`scraping-${e.source}`, e.label) } }), /* @__PURE__ */ Y("a", {
							class: "scraping-url externallink",
							href: e.login,
							target: "_blank",
							rel: "noopener noreferrer",
							children: [
								/* @__PURE__ */ Y("img", {
									src: g(e.login),
									alt: "",
									width: "16",
									height: "16",
									loading: "lazy",
									onError: (e) => e.currentTarget.remove()
								}),
								/* @__PURE__ */ Y("span", { children: e.login }),
								/* @__PURE__ */ Y("svg", {
									class: "externalmark",
									viewBox: "0 0 24 24",
									"aria-hidden": "true",
									children: /* @__PURE__ */ Y("use", { href: "#i-external-link" })
								})
							]
						})]
					}),
					/* @__PURE__ */ Y("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ Y(jn, {
							value: a,
							onChange: s
						})]
					}),
					a === "peach" && /* @__PURE__ */ Y("a", {
						class: "geist-text-link",
						href: "/configuration#peachProxy",
						children: "配置 Peach 代理"
					}),
					e.accepts_cookie && /* @__PURE__ */ Y(L, { children: [
						/* @__PURE__ */ Y("p", { children: n.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ Y("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ Y("label", { children: [/* @__PURE__ */ Y("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: p === t,
								onChange: () => {
									m(t), l(""), f(""), _("");
								}
							}), /* @__PURE__ */ Y("span", { children: n })] }, t))
						}),
						p === "paste" ? /* @__PURE__ */ Y("label", { children: ["Cookie", /* @__PURE__ */ Y("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: c,
							disabled: v,
							onInput: (e) => l(e.currentTarget.value)
						})] }) : /* @__PURE__ */ Y("label", {
							class: "scraping-file",
							children: ["Netscape Cookie 文件（.txt）", /* @__PURE__ */ Y("span", {
								class: "scraping-file-control",
								children: [
									/* @__PURE__ */ Y("span", {
										class: "geist-button",
										children: "选择文件"
									}),
									/* @__PURE__ */ Y("span", {
										class: "scraping-file-name",
										children: h || "未选择文件"
									}),
									/* @__PURE__ */ Y("input", {
										ref: w,
										type: "file",
										accept: ".txt",
										disabled: v,
										onChange: async (e) => {
											let t = e.currentTarget.files?.[0];
											if (!t) {
												f(""), _("");
												return;
											}
											if (f(""), t.size > 262144) {
												x("Cookie 文本超过 256 KiB"), e.currentTarget.value = "";
												return;
											}
											y(!0);
											try {
												let e = await t.text();
												E.current.signal.aborted || (f(e), _(t.name));
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
					b && /* @__PURE__ */ Y("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: o(b, { variant: "error" }) }
					}),
					S.map((t) => /* @__PURE__ */ Y("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: o(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ Y("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					e.accepts_cookie && n.cookie_saved && /* @__PURE__ */ Y("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void D("revoke"),
						children: "撤销 Cookie"
					}),
					/* @__PURE__ */ Y("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void D("check"),
						children: "检查连接"
					}),
					/* @__PURE__ */ Y("button", {
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
	let [r, a] = G(""), [s, c] = G(!1), [l, u] = G(""), f = J(null);
	q(() => d(f.current, s), [s]);
	let p = J(new AbortController()), m = J(0);
	async function h(e = !1) {
		let t = ++m.current;
		await On({
			read: (e) => V("/api/scraping/cover", e),
			active: () => !p.current.signal.aborted && t === m.current,
			render: (t) => {
				c(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && u(t.error || "采集未取得"), t.status === "complete" && !e && n(t.result || "封面采集完成");
			},
			disconnected: () => u("连接中断，正在重新读取后台进度")
		});
	}
	K(() => (h(!0), () => p.current.abort()), []);
	async function g() {
		if (!s) {
			m.current++, c(!0), u("");
			try {
				await H("/api/scraping/cover", { code: r }, "POST", p.current.signal), await h();
			} catch (e) {
				p.current.signal.aborted || (c(!1), u(B(e)));
			}
		}
	}
	return t ? /* @__PURE__ */ Y("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: o(t, { variant: "error" }) }
	}) : /* @__PURE__ */ Y("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ Y("p", { children: "高清图片可能需要代理才能下载，请先检查连接。" }),
			/* @__PURE__ */ Y("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ Y("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: i("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ Y("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), g();
							},
							children: [/* @__PURE__ */ Y("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: r,
								disabled: s,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => a(e.currentTarget.value)
							}), /* @__PURE__ */ Y("button", {
								ref: f,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						l && /* @__PURE__ */ Y("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: o(l, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ Y(Mn, {
				source: e,
				toast: n
			}, e.source))
		]
	});
}
//#endregion
//#region src/islands/library-processing.tsx
var Pn = (e, t) => V("/api/library-processing", t);
function Fn({ data: e, error: t, toast: n, onComplete: r, mode: s, monitor: l }) {
	let [u, f] = G(e || { status: "idle" }), [p, m] = G(t), [h, g] = G(!1), [_, v] = G(!1), y = J(new AbortController()), b = J(0), x = J(u.status), S = J(null), C = h || u.status === "running";
	q(() => d(S.current, C), [C]);
	async function w() {
		let e = ++b.current;
		await On({
			read: (e) => V("/api/library-processing", e),
			active: () => !y.current.signal.aborted && b.current === e,
			keepWatching: s === "notice" || !!l,
			render: (e) => {
				f(e), m(""), e.status === "complete" && x.current === "running" && s !== "notice" && (v(!0), n("已完成扫描与资料采集")), x.current === "running" && (e.status === "complete" || e.status === "failed") && r?.(), x.current = e.status;
			},
			disconnected: () => m("连接中断，正在重新读取处理进度")
		});
	}
	K(() => ((u.status === "running" || s === "notice" || l) && w(), () => y.current.abort()), []);
	async function T() {
		if (!C) {
			g(!0), m(""), v(!1);
			try {
				let e = await H("/api/library-processing", {}, "POST", y.current.signal);
				if (y.current.signal.aborted) return;
				x.current = e.status, f(e), g(!1), await w();
			} catch (e) {
				y.current.signal.aborted || (m(B(e)), g(!1));
			}
		}
	}
	if (s === "notice") {
		if (!p && u.status !== "running" && u.status !== "failed") return null;
		let e = p || (u.status === "failed" ? "扫描与资料采集未完成" : `${u.stage || "正在整理馆藏"}${u.total ? ` · ${u.checked || 0} / ${u.total}` : ""}`);
		return /* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: c(e, {
			variant: u.status === "failed" ? "error" : p ? "warning" : "gray",
			href: "/data-cleanup#libraryProcessing",
			label: p || u.status === "failed" ? "查看并处理" : "查看进度",
			value: u.checked || 0,
			...u.status === "running" && u.total !== void 0 ? { max: u.total } : {}
		}) } });
	}
	return /* @__PURE__ */ Y(L, { children: [/* @__PURE__ */ Y("div", {
		class: "geist-fieldset-content library-processing",
		children: [
			/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: i("cleanupScrapingTitle", "扫描与采集") } }),
			/* @__PURE__ */ Y("p", { children: "扫描媒体文件夹，导入已有资料，采集缺失信息。" }),
			/* @__PURE__ */ Y("div", {
				"aria-live": "polite",
				children: [
					u.status === "running" && /* @__PURE__ */ Y(L, { children: [/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: a(`${u.stage || "正在处理"}${u.total ? ` · ${u.checked || 0} / ${u.total}` : ""}`) } }), !!u.total && /* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: Pe(`已处理 ${u.checked || 0} / ${u.total} 个视频`, u.checked || 0, u.total) } })] }),
					(p || u.status === "failed") && /* @__PURE__ */ Y("div", {
						role: "alert",
						onClick: (e) => {
							e.target.closest("[data-note-action]") && T();
						},
						dangerouslySetInnerHTML: { __html: o(p || u.error || "处理未完成，请重试", {
							variant: "error",
							filled: !0,
							actionLabel: u.status === "failed" ? "重试未完成项" : ""
						}) }
					}),
					u.status === "failed" && !!u.issues?.length && /* @__PURE__ */ Y("ul", { children: u.issues.slice(0, 20).map((e) => /* @__PURE__ */ Y("li", { children: [
						e.asset_id ? /* @__PURE__ */ Y("a", {
							href: `/item/${e.asset_id}`,
							children: "查看视频"
						}) : null,
						e.asset_id ? "：" : "",
						e.message
					] })) }),
					_ && /* @__PURE__ */ Y("div", {
						class: "library-processing-result",
						dangerouslySetInnerHTML: { __html: o(`已扫描 ${u.scanned || 0} 个文件，识别 ${u.identified || 0} 个番号，整理 ${u.candidates || 0} 组资料候选。`, {
							variant: "success",
							label: "处理完成"
						}) }
					})
				]
			})
		]
	}), /* @__PURE__ */ Y("footer", {
		class: "geist-fieldset-footer",
		"data-geist-fieldset-footer": !0,
		children: [
			/* @__PURE__ */ Y("a", {
				class: "geist-button",
				href: "/scraping",
				children: "采集来源"
			}),
			!!u.candidates && /* @__PURE__ */ Y("a", {
				class: "geist-button",
				href: "/review",
				children: "复核资料"
			}),
			u.status !== "failed" && /* @__PURE__ */ Y("button", {
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
	let t = zn(e) || (e.startsWith("/") && !e.startsWith("//") ? e : "");
	return `<div class="reviewimage" data-review-picture><span class="reviewimageempty"${t ? " hidden" : ""}>未取得来源图片</span>${t ? `<img src="${h(t)}" alt="来源候选图片" loading="lazy">` : ""}</div>`;
}
function Vn(e) {
	let t = zn(e.profile_url), n = (e.preview_assets || []).slice(0, 6), r = Math.max(0, Number(e.video_count || e.videos || 0));
	return `<section class="reviewidentityevidence"><h5>候选身份：${h(e.babepedia_name || "未标注")}</h5>
    <div class="reviewevidenceactions">${t ? `<a class="geist-button externallink" href="${h(t)}" target="_blank" rel="noopener noreferrer">来源资料<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a>` : ""}
    <button type="button" class="geist-button" data-entity-kind="creator" data-entity-name="${h(e.creator || "")}">查看全部 ${r.toLocaleString()} 部作品</button></div>
    ${Bn(e.preview_url)}
    <p>通过后记录身份判断。</p>
    ${n.length ? `<h5>本地作品样本</h5><div class="reviewevidencesamples">${n.map((e) => `<div class="reviewevidencesample">
      <button class="geist-button" type="button" data-review-open-item="${e.id}"><span data-middle-truncate title="${h(e.name)}">${h(e.name)}</span></button>
      <button class="geist-button" type="button" data-review-reveal="${e.id}" aria-label="打开 ${h(e.name)} 的文件位置">文件位置</button>
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
				message: B(e)
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
function Xn(e, n) {
	let r = e.querySelector(".reviewlist");
	if (!r || !n.rows.length || n.locked) return;
	let i = n.state, a = [...r.querySelectorAll("[data-review-key]")];
	n.category !== void 0 && i.category !== n.category && (i.category = n.category, i.filter = "", i.groupBy = "candidates", i.anchor = null);
	let o = Gn(n.rows, n.metadata);
	o.some((e) => e[0] === i.groupBy) || (i.groupBy = "candidates", i.filter = "");
	let s = Kn(n.rows, i.groupBy);
	s.some((e) => e.key === i.filter) || (i.filter = "");
	let c = () => [...r.querySelectorAll("[data-review-key]")].filter((e) => !e.closest("[hidden]")), u = () => c().filter((e) => i.selected.has(e.dataset.reviewKey)), f = () => n.rows.filter((e) => u().some((t) => t.dataset.reviewKey === e.item_key)), m = (e) => !e.querySelector("[data-review-status=\"approved\"]")?.disabled, h = (e, t = "") => {
		let n = document.createElement("button");
		return n.type = "button", n.className = `geist-button ${t}`.trim(), n.textContent = e, n;
	}, g = document.createElement("div");
	g.className = "reviewbulkbar reviewbulktoolbar", g.setAttribute("role", "group"), g.setAttribute("aria-label", "复核批量操作");
	let _ = document.createElement("div");
	_.className = "reviewgroupby", _.innerHTML = l(o, i.groupBy, { label: "筛选分组方式" });
	let v = p(_.firstElementChild);
	_.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), v.addEventListener("change", () => {
		if (i.busy || !o.some((e) => e[0] === v.value)) return;
		i.groupBy = v.value, i.filter = "", i.anchor = null;
		let t = e.parentElement;
		n.refresh(), t?.querySelector(".reviewgroupby button")?.focus({ preventScroll: !0 });
	});
	let y = document.createElement("div");
	y.className = "reviewcategoryfilter", y.hidden = s.length < 2, y.innerHTML = l([[
		"",
		"全部分类",
		"list-filter"
	], ...s.map((e) => [
		e.key,
		`${e.title} · ${e.rows.length}`,
		"list-filter"
	])], i.filter, { label: i.groupBy === "field" ? "筛选字段分类" : "筛选当前分类" });
	let b = y.querySelector("[data-select-menu]");
	if (b) {
		let e = document.createElement("div");
		e.setAttribute("role", "group"), e.setAttribute("aria-label", i.groupBy === "field" ? "字段分类" : "当前分类");
		let t = document.createElement("div");
		t.className = "reviewfilterheading", t.textContent = e.getAttribute("aria-label"), t.setAttribute("aria-hidden", "true"), e.append(t, ...Array.from(b.children).slice(1)), b.append(e);
	}
	let x = p(y.firstElementChild);
	y.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), x.addEventListener("change", () => {
		if (i.busy || x.value && !s.some((e) => e.key === x.value)) return;
		i.filter = x.value, i.anchor = null;
		let t = e.parentElement;
		n.refresh(), t?.querySelector(".reviewcategoryfilter button")?.focus({ preventScroll: !0 });
	});
	let S = h("全选本页"), C = h("通过所选", "primary"), w = h("拒绝所选", "error"), T = document.createElement("span");
	T.className = "reviewselectedcount selectiondockcount", T.setAttribute("role", "status");
	let E = document.createElement("div");
	E.className = "reviewbulksource", E.hidden = !n.metadata;
	let D = document.createElement("p");
	D.className = "reviewstate reviewbulkfeedback", D.setAttribute("role", "status");
	let O = document.createElement("div");
	O.className = "reviewbulkdecisions", O.append(C, w);
	let k = document.createElement("div");
	k.className = "selectiondock reviewdock", k.setAttribute("role", "group"), k.setAttribute("aria-label", "复核所选项目");
	let A = h("取消选择");
	k.append(T, E, O, A, D), g.append(_, y, S);
	let j = e.querySelector(".reviewcontrols");
	j ? j.append(g) : r.before(g), e.append(k), r.classList.add("reviewgroups");
	let ee = () => {
		i.selected.clear(), i.anchor = null, P();
	};
	A.onclick = () => {
		i.busy || (ee(), S.focus({ preventScroll: !0 }));
	}, S.onclick = () => {
		if (i.busy) return;
		let e = c(), t = u().length === e.length;
		e.forEach((e) => t ? i.selected.delete(e.dataset.reviewKey) : i.selected.add(e.dataset.reviewKey)), P();
	}, C.onclick = () => F("approved", C), w.onclick = () => F("rejected", w);
	let M = [];
	for (let e of s) {
		let n = e.rows.map((e) => a.find((t) => t.dataset.reviewKey === e.item_key)).filter((e) => !!e), o = document.createElement("section");
		o.className = "reviewgroup", o.hidden = !!i.filter && e.key !== i.filter;
		let s = document.createElement("div");
		s.className = "reviewbulkbar reviewgroupbar";
		let l = document.createElement("h3");
		l.textContent = `${e.title} · ${n.length}`;
		let u = h("全选本组"), d = document.createElement("div");
		d.className = "reviewlist", s.append(l, u), o.append(s, d), r.append(o), u.onclick = () => {
			if (i.busy) return;
			let e = n.every((e) => i.selected.has(e.dataset.reviewKey));
			n.forEach((t) => e ? i.selected.delete(t.dataset.reviewKey) : i.selected.add(t.dataset.reviewKey)), P();
		}, M.push(() => {
			u.textContent = n.every((e) => i.selected.has(e.dataset.reviewKey)) ? "清空本组" : "全选本组";
		});
		for (let e of n) {
			d.append(e);
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
				qn(i, c().map((e) => e.dataset.reviewKey), n, e, t), P();
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
						let r = c(), a = r[r.indexOf(e) + (t.key === "ArrowDown" ? 1 : -1)];
						a && (i.anchor === null && (i.anchor = n), qn(i, r.map((e) => e.dataset.reviewKey), a.dataset.reviewKey, !0, !0), P(), a.querySelector(".reviewpickitem input")?.focus());
					}
				}
			}), M.push(() => {
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
				t.checked && i.choices.set(n, t.value), P();
			});
		}
	}
	e.addEventListener("keydown", (t) => {
		i.busy || !e.contains(r) || (t.key === "Escape" && i.selected.size && (t.preventDefault(), t.stopPropagation(), ee()), (t.ctrlKey || t.metaKey) && t.key.toLowerCase() === "a" && !t.target.matches("textarea,input:not([type=\"checkbox\"]):not([type=\"radio\"])") && (t.preventDefault(), t.stopPropagation(), c().forEach((e) => i.selected.add(e.dataset.reviewKey)), P()));
	});
	let N = "";
	function P() {
		let e = u();
		S.textContent = e.length === c().length ? "清空当前选择" : i.filter ? "全选当前分类" : "全选本页", k.hidden = !e.length, T.textContent = `已选 ${e.length} 项`, C.disabled = !e.length || e.some((e) => !m(e)), w.disabled = !e.length;
		let t = Yn(f());
		E.hidden = !n.metadata || !f().some((e) => (e.candidates?.length || 0) > 1);
		let r = e.length && !t.length ? "所选项目无共同来源" : "统一选择来源", a = JSON.stringify([r, t]);
		if (a !== N) {
			N = a, E.innerHTML = l([["", r], ...t.map((e) => [e, e])], "", { label: "统一选择来源" });
			let e = p(E.firstElementChild);
			e.disabled = !t.length, e.addEventListener("change", () => {
				if (!(i.busy || !Yn(f()).includes(e.value))) {
					for (let t of u()) {
						let r = n.rows.find((e) => e.item_key === t.dataset.reviewKey).candidates.find((t) => t.source === e.value);
						t.querySelectorAll("input[type=\"radio\"]").forEach((e) => {
							e.checked = e.value === r.candidate_key;
						}), i.choices.set(t.dataset.reviewKey, r.candidate_key);
					}
					D.textContent = `已选择 ${e.value}，点击通过所选采用。`;
				}
			});
		}
		M.forEach((e) => e());
	}
	async function F(t, r) {
		if (i.busy || !u().length) return;
		let a = u().map((e) => ({
			key: e.dataset.reviewKey,
			payload: {
				...n.payload(e),
				status: t
			}
		}));
		if (t === "approved" && n.metadata && a.some((e) => !e.payload.candidate_key)) {
			D.textContent = "请先为所选的多来源候选选择来源。", u().find((e) => !e.querySelector("input[type=\"radio\"]:checked"))?.querySelector("input[type=\"radio\"]")?.focus();
			return;
		}
		i.busy = !0, D.textContent = `正在处理 0 / ${a.length}`, d(r, !0);
		let o = [...e.querySelectorAll("button,input")], s = o.map((e) => e.getAttribute("aria-disabled"));
		o.forEach((e) => e.setAttribute("aria-disabled", "true"));
		let c = (e) => {
			e instanceof KeyboardEvent && e.key === "Tab" || (e.preventDefault(), e.stopImmediatePropagation());
		};
		e.addEventListener("click", c, !0), e.addEventListener("keydown", c, !0);
		let l = 0, f = await Jn(a, async (e) => {
			try {
				return await n.submit(e);
			} finally {
				l++, n.active() && (D.textContent = `正在处理 ${l} / ${a.length}`);
			}
		}, (e) => {
			i.selected.delete(e), i.errors.delete(e), n.applied(e);
		}, n.active);
		if (i.busy = !1, e.removeEventListener("click", c, !0), e.removeEventListener("keydown", c, !0), o.forEach((e, t) => {
			let n = s[t];
			n === null ? e.removeAttribute("aria-disabled") : e.setAttribute("aria-disabled", n);
		}), d(r, !1), !n.active()) return;
		n.notify(`已${t === "approved" ? "通过" : "拒绝"} ${f.completed} 项${f.failures.length ? `，${f.failures.length} 项未完成` : ""}`), f.failures.forEach((e) => i.errors.set(e.key, e.message));
		let p = e.parentElement;
		n.refresh(), p?.querySelector(".reviewbulktoolbar button")?.focus({ preventScroll: !0 });
	}
	P(), Wn(e);
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
//#region src/board-skeleton.ts
function er(e) {
	let t = (e = "60%") => `<i class="skeleton" style="width:${e}"></i>`, n = () => `<div class="board-skeleton-row">${t("36%")}${t("24%")}</div>`, r = "";
	if (e === "/stats" || e === "/taste") r = `${e === "/taste" ? `<div class="board-skeleton-row">${t("26%")}${t("32%")}</div>` : ""}<div class="metricstrip board-skeleton-metrics">${Array.from({ length: 4 }, () => `<div class="tastesummary">${t()}<b class="skeleton"></b><small class="board-stat-footer">${t("48%")}</small></div>`).join("")}</div><div class="board-skeleton-chart"><div class="board-skeleton-ring skeleton"></div><div>${n().repeat(4)}</div></div><div class="board-skeleton-section">${t("32%")}${n().repeat(5)}</div>`;
	else if (e === "/follow-manage") r = `<div class="board-skeleton-section">${t("20%")}<div class="skeleton board-skeleton-input"></div>${t("72%")}</div><div class="board-skeleton-row">${t("24%")}${t("40%")}</div><div class="board-skeleton-section">${n().repeat(6)}</div><div class="board-skeleton-row">${t("30%")}${t("30%")}</div>`;
	else if (e === "/configuration") r = `<div class="board-skeleton-row">${t("16%").repeat(4)}</div><div class="board-skeleton-section">${t("24%")}${n().repeat(3)}<div class="skeleton board-skeleton-input"></div></div><div class="board-skeleton-section">${t("24%")}${n().repeat(2)}</div>`;
	else return "";
	return `<div class="board-page-skeleton" data-skeleton="board${e}" role="status" aria-label="正在读取页面"><div aria-hidden="true">${r}</div></div>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var tr = [
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
function nr() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function rr(e, t) {
	let n = new URLSearchParams();
	for (let t of tr) e[t] && n.set(t, e[t]);
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
function ir({ kind: e = "catalog", filtered: t = !1, jav: n = !1, configurable: i = !1, online: a = !1 } = {}) {
	let o = i ? "<a class=\"geist-button primary\" href=\"/configuration\">添加内容</a>" : "", s = "<a class=\"geist-button\" href=\"/follow-manage\">添加来源</a>";
	return t || n ? r("search", n ? "还没有符合条件的 JAV 作品" : "没有符合条件的内容", n ? "已扫描但尚未补充发行资料的视频可在全部内容中查看。" : "清除筛选或搜索条件后查看全部内容。", { actions: "<a class=\"geist-button primary\" href=\"/?loc=&thumb=0\">查看全部内容</a>" }) : e === "catalog" ? r("play", "还没有视频", "添加媒体文件夹或关注来源，开始建立你的馆藏。", { actions: o + s }) : r(e === "tags" ? "tags" : "user-round", "还没有" + ({
		tags: "标签",
		performers: "艺人",
		creators: "创作者",
		studios: "厂牌",
		agencies: "事务所",
		series: "系列"
	}[e] || "资料"), a ? "添加关注来源并获取内容后，这里会显示对应标签。" : "添加内容并补充资料后，这里会显示对应信息。", { actions: a ? s : o + s });
}
//#endregion
//#region src/sidebar.ts
function ar(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function or(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function sr(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function cr(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function lr(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function ur() {
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
function dr(e, t = !1, n = !1) {
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
var fr = "peach-taste-guide-dismissed";
function pr(e, t) {
	f(e, ".taste-history-guide", "taste-guide-collapse");
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(fr, "1"), n.remove();
	});
}
//#endregion
//#region src/resource-sync.ts
var $ = (e = 0) => Number(e).toLocaleString(), mr = {
	local: "本地磁盘",
	115: "115",
	pikpak: "PikPak"
};
function hr(e, t) {
	let n = e.cache || {
		files: 0,
		bytes: 0
	}, r = !!(e.missing || n.files);
	return `<div class="resourcepanel" data-geist-fieldset><div class="resourcesources">${(e.sources || []).map((e) => `<article>
    <div class="resourcesourcetitle"><b>${mr[e.location] || "媒体来源"}</b><span class="${e.online ? "online" : "offline"}">${e.online ? "可访问" : "离线，已跳过"}</span></div>
    <strong>${e.online ? `${$(e.missing)} 项` : "—"}</strong>
    <small>${e.online ? `找不到文件 · 已检查 ${$(e.checked)} 项` : `馆藏中有 ${$(e.total)} 项`}</small>
    ${e.unreadable ? `<small>${$(e.unreadable)} 项读取失败，已跳过</small>` : ""}</article>`).join("")}</div>
    <div class="resourcecache"><div><span>可清理的缓存</span><b>${$(n.files)} 个</b><small>${t(n.bytes)}</small></div>
    <div><span>待移入回收站</span><b>${$(e.missing)} 项</b></div></div>
    ${r ? o(`将把找不到文件的 ${$(e.missing)} 项馆藏记录移入回收站，并清理 ${$(n.files)} 个闲置缓存。`, { label: "清理内容" }) : ""}
    <div class="resourceapplyrow geist-fieldset-footer" data-geist-fieldset-footer>${r ? "<button class=\"geist-button primary\" type=\"button\" id=\"resourceApply\">清理失效记录与缓存</button>" : "<p class=\"resourcesyncok\">已检查可访问的来源，没有待清理的记录或缓存。</p>"}</div></div>`;
}
//#endregion
//#region src/jav-artwork.ts
function gr(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function _r(e) {
	return {
		javLayout: gr(e.javLayout),
		javImage: vr(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function vr(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function yr(e, t) {
	return e.is_jav && e.code && e.has_cover && (vr(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function br(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (vr(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.removeAttribute("style"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var xr = {
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
		load: Ot,
		component: Ft
	}
}, Sr = () => Object.keys(xr), Cr = /* @__PURE__ */ new Map();
async function wr(e, t, n, r = {}) {
	let i = xr[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	Tr(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	Cr.set(t, a);
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
			error: B(e)
		};
	}
	if (Cr.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		Cr.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	De(ae(i.component, s), t);
}
function Tr(e) {
	let t = Cr.get(e);
	t && (t.controller.abort(), Cr.delete(e), t.painted && De(null, e));
}
//#endregion
export { fr as TASTE_GUIDE_KEY, er as boardPageSkeleton, Ae as boundedPreference, ir as catalogEmptyHtml, rr as catalogSuggestions, ur as cleanupSkeletonHtml, cr as cloudLocations, lr as cloudPreferenceLocations, Un as createReviewSelection, Fe as distributionChart, nr as emptyCatalogLayout, $n as entitySkeletonHtml, kn as followJobProgress, Vn as identityEvidenceHtml, Sr as islandNames, yr as javImageKind, Pe as jobProgressHtml, Zn as matchesFaceSource, wr as mountIsland, Me as mountNumberSetting, Qn as nativeImageFit, vr as normalizeJavImage, gr as normalizeJavLayout, _r as normalizeJavPreferences, Oe as preferredDirection, Le as radarChart, Ie as rankedChart, Rn as refreshStore, hr as resourceScanHtml, Bn as reviewImageHtml, ar as sidebarHasCatalogContent, ze as sidebarSectionHtml, sr as sidebarTagCounts, Ne as statCardBody, Ln as storeNames, br as syncJavImages, je as syncNumberSetting, or as syncSidebarSurface, dr as tasteHistoryGuideHtml, He as transitionTheme, Tr as unmountIsland, Wn as updateReviewSticky, On as watchJob, Hn as wireReviewPictures, Xn as wireReviewSelection, Be as wireSidebarGroups, pr as wireTasteHistoryGuide };
