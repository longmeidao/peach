import { LOC as e, esc as t, faviconUrl as n, fmtDur as r, fmtSize as i, icon as a, requestErrorMessage as o } from "/js/core.js";
import { MEDIA_SOURCE_ICONS as s, checkboxHtml as c, confirmModal as l, emptyStateHtml as u, fieldsetTitle as d, loadingDotsHtml as f, noteHtml as p, progressHtml as m, projectBannerHtml as h, selectFieldHtml as g, selectOptionIconHtml as _, setActionBusy as v, wireCollapse as y, wireSelectField as b } from "/js/ui-components.js";
//#region node_modules/preact/dist/preact.module.js
var x, S, C, w, T, E, D, O, k, A, j, ee, M, N, P, te = {}, ne = [], re = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, ie = Array.isArray;
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
	for (c = me(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || te, p.__i = d, g = be(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && Te(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = he(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
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
	var l, u, d, f, p, m, h, g = n.props || te, _ = t.props, v = t.type;
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
	t == document && (t = document.documentElement), S.__ && S.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], be(t, e = (!r && n || t).__k = oe(I, null, [e]), i || te, te, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? x.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), Se(a, e, o), e.props.children = null;
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
}, fe.__r = 0, k = Math.random().toString(8), A = "__d" + k, j = "__a" + k, ee = /(PointerCapture)$|Capture$/i, M = 0, N = ye(!1), P = ye(!0);
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
//#region src/board-controls.ts
function ze(e) {
	let t = Number(e.min) || 0, n = Number(e.max) || 100, r = Number(e.value), i = n > t ? Math.max(0, Math.min(100, (r - t) / (n - t) * 100)) : 0;
	e.style.setProperty("--board-range-value", `${i}%`);
	let a = e.closest(".dual-range");
	if (!a) return;
	let o = e.id === "durMax" ? "max" : "min", s = a.querySelector(`[data-range-end="${o}"]`);
	s || (s = document.createElement("output"), s.className = "board-range-tip", s.dataset.rangeEnd = o, s.setAttribute("aria-hidden", "true"), a.append(s)), s.textContent = r >= n && o === "max" ? "不限" : `${r} 分钟`, s.style.left = `${i}%`;
}
function Be() {
	let e = (e) => e.querySelectorAll("input[type=range]").forEach(ze);
	e(document), new MutationObserver((t) => {
		for (let n of t) for (let t of n.addedNodes) t instanceof Element && (t.matches("input[type=range]") && ze(t), e(t));
	}).observe(document.body, {
		subtree: !0,
		childList: !0
	}), document.addEventListener("input", (e) => {
		e.target instanceof HTMLInputElement && e.target.type === "range" && ze(e.target);
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
function Ve(e) {
	e.querySelectorAll(".tasteranks,.insightranking").forEach((e, t) => {
		if (e.children.length <= 5 || e.parentElement?.hasAttribute("data-expandable-ranks")) return;
		let n = document.createElement("div");
		n.className = "board-expand-ranks", n.dataset.expandableRanks = "", e.before(n), n.append(e), e.id = e.id || `board-rank-list-${t}`, e.classList.add("board-rank-list");
		let r = document.createElement("button");
		r.type = "button", r.className = "board-rank-expand", r.setAttribute("aria-controls", e.id), r.setAttribute("aria-expanded", "false"), r.setAttribute("aria-label", "展开更多排名"), r.innerHTML = "<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><use href=\"#i-chevron-down\"/></svg>", n.append(r);
		let i = () => {
			let t = e.children[4];
			e.offsetWidth && (n.style.setProperty("--rank-collapsed-height", `${t.offsetTop - e.offsetTop + t.offsetHeight + 20}px`), n.style.setProperty("--rank-expanded-height", `${e.scrollHeight}px`));
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
function He(e, t) {
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
function Ue(e, t) {
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
function We(e, t) {
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
function Ge(e, t) {
	return e.sourceLinks.length ? e.depth : t - 1;
}
//#endregion
//#region node_modules/d3-sankey/src/constant.js
function Ke(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-sankey/src/sankey.js
function qe(e, t) {
	return Ye(e.source, t.source) || e.index - t.index;
}
function Je(e, t) {
	return Ye(e.target, t.target) || e.index - t.index;
}
function Ye(e, t) {
	return e.y0 - t.y0;
}
function Xe(e) {
	return e.value;
}
function Ze(e) {
	return e.index;
}
function Qe(e) {
	return e.nodes;
}
function $e(e) {
	return e.links;
}
function et(e, t) {
	let n = e.get(t);
	if (!n) throw Error("missing: " + t);
	return n;
}
function tt({ nodes: e }) {
	for (let t of e) {
		let e = t.y0, n = e;
		for (let n of t.sourceLinks) n.y0 = e + n.width / 2, e += n.width;
		for (let e of t.targetLinks) e.y1 = n + e.width / 2, n += e.width;
	}
}
function nt() {
	let e = 0, t = 0, n = 1, r = 1, i = 24, a = 8, o, s = Ze, c = Ge, l, u, d = Qe, f = $e, p = 6;
	function m() {
		let e = {
			nodes: d.apply(null, arguments),
			links: f.apply(null, arguments)
		};
		return h(e), g(e), _(e), v(e), x(e), tt(e), e;
	}
	m.update = function(e) {
		return tt(e), e;
	}, m.nodeId = function(e) {
		return arguments.length ? (s = typeof e == "function" ? e : Ke(e), m) : s;
	}, m.nodeAlign = function(e) {
		return arguments.length ? (c = typeof e == "function" ? e : Ke(e), m) : c;
	}, m.nodeSort = function(e) {
		return arguments.length ? (l = e, m) : l;
	}, m.nodeWidth = function(e) {
		return arguments.length ? (i = +e, m) : i;
	}, m.nodePadding = function(e) {
		return arguments.length ? (a = o = +e, m) : a;
	}, m.nodes = function(e) {
		return arguments.length ? (d = typeof e == "function" ? e : Ke(e), m) : d;
	}, m.links = function(e) {
		return arguments.length ? (f = typeof e == "function" ? e : Ke(e), m) : f;
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
			typeof t != "object" && (t = r.source = et(n, t)), typeof i != "object" && (i = r.target = et(n, i)), t.sourceLinks.push(r), i.targetLinks.push(r);
		}
		if (u != null) for (let { sourceLinks: t, targetLinks: n } of e) t.sort(u), n.sort(u);
	}
	function g({ nodes: e }) {
		for (let t of e) t.value = t.fixedValue === void 0 ? Math.max(We(t.sourceLinks, Xe), We(t.targetLinks, Xe)) : t.fixedValue;
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
		let r = He(t, (e) => e.depth) + 1, a = (n - e - i) / (r - 1), o = Array(r);
		for (let n of t) {
			let t = Math.max(0, Math.min(r - 1, Math.floor(c.call(null, n, r))));
			n.layer = t, n.x0 = e + t * a, n.x1 = n.x0 + i, o[t] ? o[t].push(n) : o[t] = [n];
		}
		if (l) for (let e of o) e.sort(l);
		return o;
	}
	function b(e) {
		let n = Ue(e, (e) => (r - t - (e.length - 1) * o) / We(e, Xe));
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
		o = Math.min(a, (r - t) / (He(n, (e) => e.length) - 1)), b(n);
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
			l === void 0 && i.sort(Ye), w(i, n);
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
			l === void 0 && i.sort(Ye), w(i, n);
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
			for (let { source: { sourceLinks: e } } of t) e.sort(Je);
			for (let { target: { targetLinks: t } } of e) t.sort(qe);
		}
	}
	function O(e) {
		if (u === void 0) for (let { sourceLinks: t, targetLinks: n } of e) t.sort(Je), n.sort(qe);
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
var rt = Math.PI, it = 2 * rt, z = 1e-6, at = it - z;
function ot() {
	this._x0 = this._y0 = this._x1 = this._y1 = null, this._ = "";
}
function st() {
	return new ot();
}
ot.prototype = st.prototype = {
	constructor: ot,
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
		else if (d > z) {
			if (!(Math.abs(u * s - c * l) > z) || !i) this._ += "L" + (this._x1 = e) + "," + (this._y1 = t);
			else {
				var f = n - a, p = r - o, m = s * s + c * c, h = f * f + p * p, g = Math.sqrt(m), _ = Math.sqrt(d), v = i * Math.tan((rt - Math.acos((m + d - h) / (2 * g * _))) / 2), y = v / _, b = v / g;
				Math.abs(y - 1) > z && (this._ += "L" + (e + y * l) + "," + (t + y * u)), this._ += "A" + i + "," + i + ",0,0," + +(u * f > l * p) + "," + (this._x1 = e + b * s) + "," + (this._y1 = t + b * c);
			}
		}
	},
	arc: function(e, t, n, r, i, a) {
		e = +e, t = +t, n = +n, a = !!a;
		var o = n * Math.cos(r), s = n * Math.sin(r), c = e + o, l = t + s, u = 1 ^ a, d = a ? r - i : i - r;
		if (n < 0) throw Error("negative radius: " + n);
		this._x1 === null ? this._ += "M" + c + "," + l : (Math.abs(this._x1 - c) > z || Math.abs(this._y1 - l) > z) && (this._ += "L" + c + "," + l), n && (d < 0 && (d = d % it + it), d > at ? this._ += "A" + n + "," + n + ",0,1," + u + "," + (e - o) + "," + (t - s) + "A" + n + "," + n + ",0,1," + u + "," + (this._x1 = c) + "," + (this._y1 = l) : d > z && (this._ += "A" + n + "," + n + ",0," + +(d >= rt) + "," + u + "," + (this._x1 = e + n * Math.cos(i)) + "," + (this._y1 = t + n * Math.sin(i))));
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
function ct(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-shape/src/point.js
function lt(e) {
	return e[0];
}
function ut(e) {
	return e[1];
}
//#endregion
//#region node_modules/d3-shape/src/array.js
var dt = Array.prototype.slice;
//#endregion
//#region node_modules/d3-shape/src/link/index.js
function ft(e) {
	return e.source;
}
function pt(e) {
	return e.target;
}
function mt(e) {
	var t = ft, n = pt, r = lt, i = ut, a = null;
	function o() {
		var o, s = dt.call(arguments), c = t.apply(this, s), l = n.apply(this, s);
		if (a ||= o = st(), e(a, +r.apply(this, (s[0] = c, s)), +i.apply(this, s), +r.apply(this, (s[0] = l, s)), +i.apply(this, s)), o) return a = null, o + "" || null;
	}
	return o.source = function(e) {
		return arguments.length ? (t = e, o) : t;
	}, o.target = function(e) {
		return arguments.length ? (n = e, o) : n;
	}, o.x = function(e) {
		return arguments.length ? (r = typeof e == "function" ? e : ct(+e), o) : r;
	}, o.y = function(e) {
		return arguments.length ? (i = typeof e == "function" ? e : ct(+e), o) : i;
	}, o.context = function(e) {
		return arguments.length ? (a = e ?? null, o) : a;
	}, o;
}
function ht(e, t, n, r, i) {
	e.moveTo(t, n), e.bezierCurveTo(t = (t + r) / 2, n, t, i, r, i);
}
function gt() {
	return mt(ht);
}
//#endregion
//#region node_modules/d3-sankey/src/sankeyLinkHorizontal.js
function _t(e) {
	return [e.source.x1, e.y0];
}
function vt(e) {
	return [e.target.x0, e.y1];
}
function yt() {
	return gt().source(_t).target(vt);
}
//#endregion
//#region src/board-sankey.ts
function bt(e = []) {
	let n = e.filter((e) => e.source && e.target && Number.isFinite(e.value) && e.value > 0);
	if (!n.length) return "";
	let r = [...new Set(n.map((e) => e.source))], i = [...new Set(n.map((e) => e.target))], a = nt().nodeId((e) => e.id).nodeWidth(10).nodePadding(22).extent([[155, 16], [535, 404]])({
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
	}), o = n.reduce((e, t) => e + t.value, 0), s = yt(), c = a.links.map((e) => {
		let n = e.source, i = e.target;
		return `<path d="${s(e)}" stroke-width="${Math.max(.5, e.width || 0)}" style="--flow-color:var(--board-chart-${r.indexOf(n.name) % 6})" data-flow-source="${n.index}" data-flow-target="${i.index}" data-flow-value="${e.value}" data-flow-label="${t(n.name)} → ${t(i.name)}" tabindex="0" role="img" aria-label="${t(n.name)} → ${t(i.name)}：${e.value} 条线索"/>`;
	}).join(""), l = a.nodes.map((e) => `<g data-flow-node="${e.index}" data-flow-value="${e.value}" data-flow-label="${t(e.name)}" tabindex="0" role="img" aria-label="${t(e.name)}：${e.value} 条线索"><rect x="${e.x0}" y="${e.y0}" width="10" height="${Math.max(1, (e.y1 || 0) - (e.y0 || 0))}" rx="5" fill="${e.side === "source" ? `var(--board-chart-${r.indexOf(e.name) % 6})` : "var(--color-text-secondary)"}"/><text x="${e.side === "source" ? 145 : 545}" y="${((e.y0 || 0) + (e.y1 || 0)) / 2}" text-anchor="${e.side === "source" ? "end" : "start"}" dominant-baseline="middle">${t(e.name.length > 18 ? e.name.slice(0, 16) + "…" : e.name)}<tspan x="${e.side === "source" ? 145 : 545}" dy="15">${e.side === "source" ? e.value?.toLocaleString() : ((e.value || 0) / o * 100).toFixed(1) + "%"}</tspan></text></g>`).join("");
	return `<section class="board-sankey-card" data-sankey-card><header><h3>创作者线索来源</h3><b data-sankey-number>${o.toLocaleString()}</b><span data-sankey-label>条线索</span></header><div class="board-sankey-scroll"><svg viewBox="0 0 720 435" aria-label="来源网站与创作者线索"><g class="board-sankey-links">${c}</g><g class="board-sankey-nodes">${l}</g></svg></div><footer><span>来源网站</span><span>创作者 · 线索占比</span></footer></section>`;
}
function xt(e) {
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
var St = (e) => Number.isFinite(e) && e >= 0;
function Ct(e, n, r = "个视频") {
	let i = e.filter((e) => St(e.value));
	if (!i.length) return "";
	let a = i.reduce((e, t) => e + t.value, 0), o = Math.max(1, ...i.map((e) => e.value)) * 1.1, s = Math.min(22, 110 / Math.max(1, i.length)), c = Math.min(15, s * .68), l = i.map((e, n) => {
		let i = 32 + n * s, a = e.value / o * 100;
		return `<g style="--ring-color:var(--board-chart-${n % 6});--ring-delay:${n * 60}ms"><circle class="board-ring-track" cx="160" cy="160" r="${i}" stroke-width="${c}"/><circle class="board-ring-value" data-radial-ring="${n}" tabindex="0" role="button" aria-label="${t(e.name)}：${e.value.toLocaleString()} ${t(r)}" aria-pressed="false" cx="160" cy="160" r="${i}" stroke-width="${c}" pathLength="100" stroke-dasharray="${a} ${100 - a}" style="--ring-length:${a}" transform="rotate(-90 160 160)"/></g>`;
	}).join("");
	return `<section class="board-radial-card" data-radial-card data-radial-total="${a}" data-radial-title="${t(n)}"><header><span data-radial-label>${t(n)}</span><b data-radial-number>${a.toLocaleString()}</b><small>${t(r)}</small></header><svg class="board-rings" viewBox="0 0 320 320" aria-label="${t(n)}">${l}</svg><div class="board-radial-tiles">${i.map((e, n) => `<button type="button" data-radial-tile="${n}" data-radial-value="${e.value}" data-radial-name="${t(e.name)}" aria-pressed="false" style="--ring-color:var(--board-chart-${n % 6})"><span><i aria-hidden="true"></i>${t(e.name)}</span><b>${e.value.toLocaleString()}</b>${e.detail ? `<small>${t(e.detail)}</small>` : ""}</button>`).join("")}</div></section>`;
}
function wt(e) {
	e.querySelectorAll("[data-radial-card]").forEach((e) => {
		let t = [...e.querySelectorAll("[data-radial-tile]")], n = [...e.querySelectorAll("[data-radial-ring]")], r = e.querySelector("[data-radial-number]"), i = e.querySelector("[data-radial-label]"), a = -1, o = 0, s = 0, c = (c) => {
			e.dataset.radialFocus = String(c), t.forEach((e, t) => {
				e.dataset.active = String(t === c), e.setAttribute("aria-pressed", String(t === a)), n[t]?.setAttribute("aria-pressed", String(t === a)), n[t] && (n[t].dataset.active = String(t === c));
			});
			let l = Number(c < 0 ? e.dataset.radialTotal : t[c]?.dataset.radialValue);
			i.textContent = c < 0 ? e.dataset.radialTitle : t[c].dataset.radialName, cancelAnimationFrame(s);
			let u = o, d = performance.now(), f = (e) => {
				let t = matchMedia("(prefers-reduced-motion: reduce)").matches ? 1 : Math.min(1, (e - d) / 300);
				o = u + (l - u) * (1 - (1 - t) ** 3), r.textContent = Math.round(o).toLocaleString(), t < 1 && (s = requestAnimationFrame(f));
			};
			s = requestAnimationFrame(f);
		}, l = (e) => {
			a = a === e ? -1 : e, c(a);
		};
		[...t, ...n].forEach((e) => {
			let t = Number(e.getAttribute("data-radial-tile") ?? e.getAttribute("data-radial-ring"));
			e.addEventListener("pointerenter", () => c(t)), e.addEventListener("pointerleave", () => c(a)), e.addEventListener("focus", () => c(t)), e.addEventListener("blur", () => c(a)), e.addEventListener("click", () => l(t)), e instanceof SVGElement && e.addEventListener("keydown", (e) => {
				(e.key === "Enter" || e.key === " ") && (e.preventDefault(), l(t));
			});
		}), c(-1);
	});
}
var Tt = [
	"周一",
	"周二",
	"周三",
	"周四",
	"周五",
	"周六",
	"周日"
];
function Et(e) {
	if (!e?.days?.length) return "<section class=\"board-activity-empty\"><h3>浏览活跃时间</h3><p>还没有可用于分析的口味网站访问记录。</p></section>";
	let n = Array.from({ length: 7 }, () => Array(24).fill(0));
	for (let t of e.hours || []) Number.isInteger(t.weekday) && t.weekday >= 0 && t.weekday < 7 && Number.isInteger(t.hour) && t.hour >= 0 && t.hour < 24 && St(t.count) && (n[t.weekday][t.hour] = (n[t.weekday][t.hour] || 0) + t.count);
	let r = Math.max(1, ...n.flat()), i = n.flat().reduce((e, t) => e + t, 0), a = n.map((e, t) => `<span class="board-heat-axis">${Tt[t]}</span>${e.map((e, n) => `<button type="button" data-heat-value="${e}" data-heat-label="${Tt[t]} ${n}:00" aria-label="${Tt[t]} ${n}:00，${e} 次访问" style="--heat:${e ? Math.max(12, e / r * 100) : 0}%"></button>`).join("")}`).join(""), o = e.days.filter((e) => /^\d{4}-\d{2}-\d{2}$/.test(e.date) && St(e.count)).sort((e, t) => e.date.localeCompare(t.date));
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
function Dt(e) {
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
var Ot = (e) => e.replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function kt(e, t, n = "", r = "") {
	if (!t) return "";
	let i = `sidebar-group-${encodeURIComponent(e)}`;
	return `<details class="sec${r ? " cat-" + Ot(r) : ""}" data-sidebar-group="${Ot(e)}"><summary role="button" class="board-section-toggle"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${Ot(e)}</span>${n}</summary><div class="board-sidebar-body" id="${i}">${t}</div></details>`;
}
function At(e) {
	e.querySelectorAll("[data-sidebar-group]").forEach((e) => {
		if (e.dataset.sidebarWired) return;
		e.dataset.sidebarWired = "true";
		let t = e.querySelector(".board-section-toggle"), n = e.querySelector(".board-sidebar-body"), r = `peach.sidebar.group.${e.dataset.sidebarGroup}`, i = null;
		try {
			i = sessionStorage.getItem(r);
		} catch {}
		let a = !!n.querySelector("[aria-pressed=true]");
		e.open = i === null ? a || e.classList.contains("cat-src") || e.dataset.sidebarGroup === "时长" : i === "open", t.querySelectorAll("button").forEach((e) => e.addEventListener("click", (e) => e.stopPropagation()));
	}), y(e, "details[data-sidebar-group]", "sidebar-collapse"), e.querySelectorAll(".board-section-toggle").forEach((e) => {
		e.dataset.persistWired || (e.dataset.persistWired = "true", e.addEventListener("click", () => {
			let t = `peach.sidebar.group.${e.closest("[data-sidebar-group]").dataset.sidebarGroup}`;
			try {
				sessionStorage.setItem(t, e.getAttribute("aria-expanded") === "true" ? "open" : "closed");
			} catch {}
		}));
	});
}
var jt = !1;
async function Mt(e, t) {
	if (jt) return;
	if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
		t();
		return;
	}
	let n = e.getBoundingClientRect(), r = n.left + n.width / 2, i = n.top + n.height / 2, a = Math.hypot(Math.max(r, innerWidth - r), Math.max(i, innerHeight - i)) * 2.5, o = document.createElement("style");
	o.textContent = `::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20100%20100%22%3E%3Cdefs%3E%3Cfilter%20id%3D%22b%22%20x%3D%22-50%25%22%20y%3D%22-50%25%22%20width%3D%22200%25%22%20height%3D%22200%25%22%3E%3CfeGaussianBlur%20stdDeviation%3D%222%22%2F%3E%3C%2Ffilter%3E%3C%2Fdefs%3E%3Ccircle%20cx%3D%2250%22%20cy%3D%2250%22%20r%3D%2242%22%20fill%3D%22white%22%20filter%3D%22url(%23b)%22%2F%3E%3C%2Fsvg%3E");mask-repeat:no-repeat;animation:peach-theme-reveal 820ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${r}px ${i}px;mask-size:0px 0px}to{mask-position:${r - a / 2}px ${i - a / 2}px;mask-size:${a}px ${a}px}}`, jt = !0, document.head.append(o);
	try {
		await document.startViewTransition(t).finished;
	} catch {
		t();
	} finally {
		o.remove(), jt = !1;
	}
}
//#endregion
//#region src/api.ts
var Nt = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(o(e, t)), this.name = "ApiError", this.status = t, this.body = n;
	}
}, Pt = (e) => {
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
}, B = (e) => o(e);
async function V(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new Nt(Pt(r) || `请求失败（${n.status}）`, n.status);
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
	if (!i.ok) throw new Nt(Pt(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var Ft, U, It, Lt, Rt = 0, zt = [], W = S, Bt = W.__b, Vt = W.__r, Ht = W.diffed, Ut = W.__c, Wt = W.unmount, Gt = W.__;
function Kt(e, t) {
	W.__h && W.__h(U, e, Rt || t), Rt = 0;
	var n = U.__H || (U.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function G(e) {
	return Rt = 1, qt(tn, e);
}
function qt(e, t, n) {
	var r = Kt(Ft++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : tn(void 0, t), function(e) {
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
	var n = Kt(Ft++, 3);
	!W.__s && en(n.__H, t) && (n.__ = e, n.u = t, U.__H.__h.push(n));
}
function q(e, t) {
	var n = Kt(Ft++, 4);
	!W.__s && en(n.__H, t) && (n.__ = e, n.u = t, U.__h.push(n));
}
function J(e) {
	return Rt = 5, Jt(function() {
		return { current: e };
	}, []);
}
function Jt(e, t) {
	var n = Kt(Ft++, 7);
	return en(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function Yt() {
	for (var e; e = zt.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(Qt), t.__h.some($t), t.__h = [];
		} catch (n) {
			t.__h = [], W.__e(n, e.__v);
		}
	}
}
W.__b = function(e) {
	U = null, Bt && Bt(e);
}, W.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), Gt && Gt(e, t);
}, W.__r = function(e) {
	Vt && Vt(e), Ft = 0;
	var t = (U = e.__c).__H;
	t && (It === U ? (t.__h = [], U.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(Qt), t.__h.some($t), t.__h = [], Ft = 0)), It = U;
}, W.diffed = function(e) {
	Ht && Ht(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (zt.push(t) !== 1 && Lt === W.requestAnimationFrame || ((Lt = W.requestAnimationFrame) || Zt)(Yt)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), It = U = null;
}, W.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(Qt), e.__h = e.__h.filter(function(e) {
				return !e.__ || $t(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], W.__e(n, e.__v);
		}
	}), Ut && Ut(e, t);
}, W.unmount = function(e) {
	Wt && Wt(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			Qt(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && W.__e(t, n.__v));
};
var Xt = typeof requestAnimationFrame == "function";
function Zt(e) {
	var t, n = function() {
		clearTimeout(r), Xt && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	Xt && (t = requestAnimationFrame(n));
}
function Qt(e) {
	var t = U, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), U = t;
}
function $t(e) {
	var t = U;
	e.__c = e.__(), U = t;
}
function en(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function tn(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var nn = 0;
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
		__v: --nn,
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
function rn({ id: e, label: t, value: n, onInput: r, error: i, help: a, current: o = !1, disabled: s = !1 }) {
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
function an({ initial: e, receipt: t }) {
	let [n, r] = G(e), [i, a] = G(""), [o, s] = G(""), [c, l] = G(""), [u, f] = G(!1), [m, h] = G(""), [g, _] = G({}), y = J(null), b = J(!1), x = J(null);
	return /* @__PURE__ */ Y("form", {
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
				let e = await H("/api/configuration/access", {
					revision: n.revision,
					action: u ? "disable" : "set",
					confirm_disable: u,
					current_password: i,
					password: u ? "" : o,
					confirmation: u ? "" : c
				});
				r(e), a(""), s(""), l(""), f(!1), _({}), t(e.mode === "open" ? "已关闭访问密码" : "已保存访问密码");
			} catch (e) {
				let t = e instanceof Nt ? e.body : null, n = t?.errors || t?.detail?.errors;
				n ? _(n) : h(B(e));
			} finally {
				b.current = !1, v(x.current, !1);
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
					children: [/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: d("accessTitle", "访问密码") } }), /* @__PURE__ */ Y("p", {
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
							checked: u,
							onChange: (e) => f(e.currentTarget.checked)
						}), /* @__PURE__ */ Y("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ Y("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ Y("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ Y("span", { children: "关闭访问密码，允许能连接到 Peach 的设备直接访问" })]
				}) : null,
				n.mode === "password" ? /* @__PURE__ */ Y(rn, {
					id: "access-current",
					label: "当前访问密码",
					value: i,
					onInput: a,
					error: g.current_password,
					current: !0
				}) : null,
				n.mode === "locked" ? null : /* @__PURE__ */ Y(I, { children: [/* @__PURE__ */ Y(rn, {
					id: "access-password",
					label: n.mode === "password" ? "新访问密码" : "设置访问密码",
					value: o,
					onInput: s,
					disabled: u,
					error: u ? void 0 : g.password,
					help: u ? "关闭访问密码时无需填写。" : "至少 8 个字符。保存后其他设备需要重新登录。"
				}), /* @__PURE__ */ Y(rn, {
					id: "access-confirm",
					label: "确认访问密码",
					value: c,
					onInput: l,
					disabled: u,
					error: u ? void 0 : g.confirmation
				})] }),
				u && /* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: p("保存后，能连接到 Peach 的设备将直接访问馆藏。", {
					variant: "warning",
					label: "访问范围"
				}) } }),
				m ? /* @__PURE__ */ Y("p", {
					class: "configbad",
					role: "alert",
					children: m
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
var on = /* @__PURE__ */ new Set([
	"downloading",
	"verifying",
	"extracting",
	"preparing",
	"restarting",
	"installing"
]);
function sn({ initial: e, initialJob: t }) {
	let [n, r] = G(e), [i, a] = G(t || {
		state: "idle",
		progress: 0
	}), [o, s] = G(""), c = J(null), u = J(!0), f = J(!1), h = J(null);
	K(() => {
		v(h.current, on.has(i.state));
	}, [i.state]), K(() => () => {
		u.current = !1, c.current?.abort();
	}, []);
	let g = async () => {
		let e = await H("/api/configuration/update-restart", {});
		u.current && a(e);
	};
	K(() => {
		i.state !== "ready" || f.current || (f.current = !0, l({
			title: "更新已准备好",
			body: `Peach ${i.version || ""} 将在重启后安装。`,
			confirmLabel: "立即重启",
			cancelLabel: "稍后",
			onConfirm: g
		}));
	}, [i.state]), K(() => {
		if (!on.has(i.state)) return;
		let e = new AbortController(), t, n = 0, o = async () => {
			try {
				let t = await V("/api/configuration/update-status", e.signal);
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
		if (c.current || on.has(i.state)) return;
		let t = new AbortController();
		c.current = t, f.current = !1, s(""), v(e, !0);
		try {
			let e = await H("/api/configuration/update", {}, "POST", t.signal);
			t.signal.aborted || a(e);
		} catch (e) {
			t.signal.aborted || s(B(e));
		} finally {
			c.current = null, v(e, !1);
		}
	}, y = async (t) => {
		if (c.current) return;
		let n = new AbortController();
		c.current = n, v(t, !0), s("");
		try {
			let e = await V("/api/configuration/updates", n.signal);
			n.signal.aborted || r(e);
		} catch (t) {
			n.signal.aborted || (r({
				...e,
				state: "error"
			}), s(B(t)));
		} finally {
			c.current = null, v(t, !1);
		}
	};
	return /* @__PURE__ */ Y("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configUpdatesTitle",
		children: [/* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: d("configUpdatesTitle", "检查更新") } }),
				/* @__PURE__ */ Y("dl", {
					class: "configfacts",
					children: [
						/* @__PURE__ */ Y("dt", { children: "当前版本" }),
						/* @__PURE__ */ Y("dd", { children: n.current_version }),
						/* @__PURE__ */ Y("dt", { children: "安装方式" }),
						/* @__PURE__ */ Y("dd", { children: n.installation }),
						/* @__PURE__ */ Y("dt", { children: "更新通道" }),
						/* @__PURE__ */ Y("dd", { children: n.channel }),
						/* @__PURE__ */ Y("dt", { children: "最新版本" }),
						/* @__PURE__ */ Y("dd", { children: n.latest_version || (n.state === "unchecked" ? "尚未检查" : "未取得") })
					]
				}),
				n.state === "available" && !o ? /* @__PURE__ */ Y("div", {
					role: "status",
					dangerouslySetInnerHTML: { __html: p(n.message, { label: "有可用更新" }) }
				}) : /* @__PURE__ */ Y("p", {
					class: o || n.state === "error" ? "configbad" : "confighelp",
					role: o || n.state === "error" ? "alert" : "status",
					children: o || n.message
				}),
				i.state === "idle" ? null : /* @__PURE__ */ Y("div", {
					"aria-live": "polite",
					children: [/* @__PURE__ */ Y("p", {
						class: i.state === "error" ? "configbad" : "confighelp",
						children: i.message
					}), i.state === "error" ? null : /* @__PURE__ */ Y(I, { children: [
						/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: m("更新准备进度：下载、校验、解压、准备安装", i.progress, 100, { stops: [
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
							children: ["下载 → 校验 → 解压 → 准备安装 · ", i.message]
						}),
						/* @__PURE__ */ Y("p", {
							class: "confighelp",
							children: i.state === "downloading" && i.total ? `${((i.downloaded || 0) / 1048576).toFixed(1)} / ${(i.total / 1048576).toFixed(1)} MB` : `${i.progress}%`
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
					href: n.release_url,
					target: "_blank",
					rel: "noreferrer",
					children: ["查看发布页", /* @__PURE__ */ Y("svg", {
						class: "externalmark",
						viewBox: "0 0 24 24",
						"aria-hidden": "true",
						children: /* @__PURE__ */ Y("use", { href: "#i-external-link" })
					})]
				}),
				i.state === "ready" ? /* @__PURE__ */ Y("button", {
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
				n.state === "available" && n.installation === "独立测试包" && i.state !== "ready" ? /* @__PURE__ */ Y("button", {
					ref: h,
					type: "button",
					class: "geist-button primary",
					onClick: (e) => _(e.currentTarget),
					children: "下载并安装"
				}) : null,
				/* @__PURE__ */ Y("button", {
					type: "button",
					class: "geist-button",
					disabled: on.has(i.state),
					onClick: (e) => y(e.currentTarget),
					children: "检查更新"
				})
			]
		})]
	});
}
//#endregion
//#region src/islands/peach-proxy.tsx
function cn({ initial: e, receipt: t }) {
	let [n, r] = G(e), [i, a] = G(e.mode), [o, s] = G(""), [c, l] = G(""), u = J(!1), f = J(null), p = J(null), m = J(new AbortController());
	K(() => () => m.current.abort(), []), q(() => {
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
				let e = await H("/api/configuration/peach-proxy", {
					mode: i,
					proxy: o
				}, "POST", m.current.signal);
				m.current.signal.aborted || (r(e), s(""), t("已保存 Peach 代理"));
			} catch (e) {
				m.current.signal.aborted || l(B(e));
			} finally {
				u.current = !1, v(p.current, !1);
			}
		}
	}
	return /* @__PURE__ */ Y("form", {
		id: "peachProxy",
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), h();
		},
		children: [/* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ Y("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: d("peachProxyTitle", "Peach 代理") } }), /* @__PURE__ */ Y("p", {
						class: "confighelp",
						children: "采集来源选择“Peach 代理”时共用此设置。"
					})]
				}),
				/* @__PURE__ */ Y("div", { ref: f }),
				i === "proxy" && /* @__PURE__ */ Y("div", {
					class: "configfield",
					children: [/* @__PURE__ */ Y("label", {
						htmlFor: "peachProxyAddress",
						children: "代理地址"
					}), /* @__PURE__ */ Y("input", {
						id: "peachProxyAddress",
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: o,
						placeholder: n.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						onInput: (e) => s(e.currentTarget.value)
					})]
				}),
				n.needs_selection && /* @__PURE__ */ Y("p", {
					class: "configbad",
					children: "已有来源的代理地址不同，请选择公共连接方式。"
				}),
				c && /* @__PURE__ */ Y("p", {
					class: "configbad",
					role: "alert",
					children: c
				})
			]
		}), /* @__PURE__ */ Y("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ Y("button", {
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
function ln({ label: e, checked: t, disabled: n, change: r }) {
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
function un({ label: e, checked: t, disabled: n, change: r }) {
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
function dn({ startup: e, receipt: t }) {
	let [n, r] = G(e.enabled), [i, a] = G(e.silent), [o, s] = G(e.desktop), [c, l] = G(""), u = J(!1), f = J(null), p = e.available && !e.desktop_message;
	async function m() {
		if (!u.current) {
			u.current = !0, v(f.current, !0), l("");
			try {
				await H("/api/configuration/startup", {
					enabled: n,
					silent: i,
					desktop: o
				}), t("已保存开机自启");
			} catch (e) {
				l(B(e));
			} finally {
				u.current = !1, v(f.current, !1);
			}
		}
	}
	return /* @__PURE__ */ Y("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), m();
		},
		children: [/* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: d("startupTitle", "开机自启") } }),
				/* @__PURE__ */ Y("div", {
					class: "configoptions",
					role: "group",
					"aria-labelledby": "startupTitle",
					children: [
						/* @__PURE__ */ Y(un, {
							label: "开机后启动 Peach",
							checked: n,
							disabled: !e.available,
							change: r
						}),
						/* @__PURE__ */ Y("div", {
							class: "configoption",
							children: [/* @__PURE__ */ Y(un, {
								label: "静默启动",
								checked: i,
								disabled: !e.available || !n,
								change: a
							}), /* @__PURE__ */ Y("p", {
								class: "confighelp",
								children: "静默启动仅显示托盘，开机后启动 Peach 打开时生效。"
							})]
						}),
						/* @__PURE__ */ Y("div", {
							class: "configoption",
							children: [/* @__PURE__ */ Y(un, {
								label: "在桌面创建快捷方式",
								checked: o,
								disabled: !p,
								change: s
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
				c && /* @__PURE__ */ Y("p", {
					class: "configbad",
					role: "alert",
					children: c
				})
			]
		}), /* @__PURE__ */ Y("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ Y("button", {
				ref: f,
				type: "submit",
				class: "geist-button primary",
				disabled: !e.available,
				children: "保存配置"
			})
		})]
	});
}
function fn({ data: e }) {
	let t = J(null);
	return q(() => {
		let n = t.current, r = document.createElement("details");
		r.className = "configdirectories";
		let i = document.createElement("summary");
		i.innerHTML = a("chevron-right") + "<span>数据目录</span>", r.append(i);
		for (let t of [.../* @__PURE__ */ new Set([e.data_root, ...e.directories])]) {
			let e = document.createElement("p");
			e.className = "confighelp", e.textContent = t, r.append(e);
		}
		return n.replaceChildren(r), y(n, "details", "uninstall-data"), () => n.replaceChildren();
	}, [e]), /* @__PURE__ */ Y("div", { ref: t });
}
function pn({ uninstall: e }) {
	let [t, n] = G(!1), [r, i] = G("");
	async function a() {
		await l({
			title: "卸载 Peach",
			danger: !0,
			body: t ? "将退出 Peach，移除程序、开机自启、桌面图标、设置、本地数据库、观看记录、凭据和缓存。原始媒体文件保留。" : "将退出 Peach 并移除程序、开机自启和桌面图标。设置、本地数据库、观看记录与缓存保留。",
			confirmLabel: "卸载 Peach",
			onConfirm: async () => {
				let e = await H("/api/configuration/uninstall", {
					delete_data: t,
					confirmation: "卸载 Peach"
				});
				i(e.message);
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
					children: [/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: d("uninstallTitle", "卸载 Peach") } }), e.available && /* @__PURE__ */ Y("p", {
						class: "confighelp",
						children: "卸载会退出 Peach、移除程序、开机自启和桌面图标。原始媒体文件保留。"
					})]
				}),
				/* @__PURE__ */ Y(ln, {
					label: "完全卸载：同时删除设置、本地数据库、观看记录、凭据和缓存",
					checked: t,
					disabled: !e.full_available || !!r,
					change: n
				}),
				/* @__PURE__ */ Y(fn, { data: e }),
				e.message && /* @__PURE__ */ Y("p", {
					class: "confighelp",
					children: e.message
				}),
				r && /* @__PURE__ */ Y("p", {
					class: "confighelp",
					role: "status",
					children: r
				})
			]
		}), /* @__PURE__ */ Y("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ Y("button", {
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
var mn = [
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
function hn() {
	let e = J(null);
	return q(() => {
		e.current && y(e.current, "details", "clouddrive-guide");
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
					] }) }), /* @__PURE__ */ Y("tbody", { children: mn.map((e) => /* @__PURE__ */ Y("tr", { children: [
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
var gn = "/api/configuration", _n = "/api/pick-folder", vn = 8e3, yn = (e, t) => V(gn, t), bn = ({ html: e, class: t }) => /* @__PURE__ */ Y("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), xn = (e) => !(e instanceof Nt) || e.status !== 400 ? null : e.body?.errors ?? null;
function Sn({ facts: e }) {
	return /* @__PURE__ */ Y("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ Y(bn, { html: d("configFactsTitle", "运行信息") }), /* @__PURE__ */ Y("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ Y(I, { children: [/* @__PURE__ */ Y("dt", { children: e.term }), /* @__PURE__ */ Y("dd", { children: [e.value, e.download_url ? /* @__PURE__ */ Y("span", {
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
function Cn({ data: e }) {
	let [t, n] = G(e.media_sources), [r, i] = G(""), a = J(null);
	K(() => () => a.current?.abort(), []);
	let o = async (e) => {
		if (a.current) return;
		let t = new AbortController();
		a.current = t, v(e, !0), i("");
		try {
			let e = await V(gn, t.signal);
			t.signal.aborted || n(e.media_sources);
		} catch (e) {
			t.signal.aborted || i(B(e));
		} finally {
			a.current = null, v(e, !1);
		}
	};
	return t ? /* @__PURE__ */ Y("section", {
		class: "configfieldset",
		"aria-labelledby": "configMountsTitle",
		children: [/* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ Y(bn, { html: d("configMountsTitle", "挂载状态") }),
				/* @__PURE__ */ Y("dl", {
					class: "configfacts",
					children: t.map((e) => /* @__PURE__ */ Y(I, { children: [/* @__PURE__ */ Y("dt", { children: [/* @__PURE__ */ Y("span", {
						"aria-hidden": "true",
						dangerouslySetInnerHTML: { __html: _(s[e.location]) }
					}), {
						local: "本地磁盘",
						115: "CloudDrive · 115",
						pikpak: "CloudDrive · PikPak"
					}[e.location] || e.location] }), /* @__PURE__ */ Y("dd", { children: [
						e.path || "未配置挂载点",
						" ",
						/* @__PURE__ */ Y("span", {
							class: `configstatus ${e.online === !0 ? "online" : e.online === !1 ? "offline" : "unknown"}`,
							children: e.online === !0 ? "在线" : e.online === !1 ? "离线" : "未检测"
						})
					] })] }))
				}),
				r ? /* @__PURE__ */ Y("p", {
					class: "configbad",
					role: "alert",
					children: r
				}) : null
			]
		}), /* @__PURE__ */ Y("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ Y("button", {
				type: "button",
				class: "geist-button",
				onClick: (e) => o(e.currentTarget),
				children: "刷新挂载状态"
			})
		})]
	}) : null;
}
function wn({ value: e, label: t, onChange: n, libraryIcon: r = !1 }) {
	let i = J(null), a = J(null), o = J(n);
	return o.current = n, q(() => {
		let n = i.current;
		n.innerHTML = g((r ? [
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
		]).map(([e, t]) => [
			e,
			t,
			s[e] || e || "database"
		]), e, { label: t });
		let c = b(n.firstElementChild);
		a.current = c;
		let l = () => o.current(c.value);
		return c.addEventListener("change", l), () => {
			a.current = null, c.disabled = !0, c.removeEventListener("change", l), n.replaceChildren();
		};
	}, [t, r]), q(() => {
		a.current && (a.current.value = e);
	}, [e]), /* @__PURE__ */ Y("div", {
		ref: i,
		class: "configsourcecontrol"
	});
}
function Tn({ data: e, receipt: t }) {
	let n = e.media_sources?.filter((e) => [
		"local",
		"115",
		"pikpak"
	].includes(e.location)), [r, i] = G(n?.length ? n.map((e) => e.path) : e.media_dirs.length ? e.media_dirs : [""]), [a, o] = G(n?.map((e) => e.location) ?? []), [s, c] = G(n?.map((e) => e.root) ?? []), [l, u] = G(n?.map((e) => e.library || "") ?? []), [f, m] = G(n?.map((e) => e.library_icon || "") ?? []), [h, g] = G(String(e.port)), [_, y] = G(!1), [b, x] = G([]), [S, C] = G(""), [w, T] = G(""), [E, D] = G(null), [O, k] = G(null), A = J(!1), j = J(e.revision), ee = J([]), M = J(null);
	q(() => {
		O !== null && (ee.current[O]?.focus(), k(null));
	}, [O]), K(() => {
		if (!E) return;
		let e = setTimeout(() => location.assign(E.url), vn);
		return () => clearTimeout(e);
	}, [E]);
	let N = (e, t) => {
		i((n) => n.map((n, r) => r === e ? t : n));
	}, P = () => {
		k(r.length), i((e) => [...e, ""]);
	}, te = (e) => {
		o((t) => t.filter((t, n) => n !== e)), c((t) => t.filter((t, n) => n !== e)), u((t) => t.filter((t, n) => n !== e)), m((t) => t.filter((t, n) => n !== e)), i((t) => t.filter((t, n) => n !== e)), x((t) => t.filter((t, n) => n !== e));
	}, ne = (e, t) => {
		x((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, re = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			v(t, !0);
			try {
				let { path: t } = await H(_n, { initial: r[e] ?? "" });
				t && (N(e, t), ne(e, ""));
			} catch (t) {
				ne(e, B(t));
			} finally {
				v(t, !1);
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
				A.current = !0, v(M.current, !0), T("");
				try {
					let n = await H(gn, {
						revision: j.current,
						media_dirs: r,
						...e.media_sources ? { media_sources: r.map((e, t) => ({
							path: e,
							location: a[t] || "local",
							root: s[t] || "",
							library: l[t] || "",
							library_icon: f[t] || ""
						})) } : {},
						port: h,
						scan_now: _
					});
					j.current = n.revision, x([]), C(""), t("已保存配置"), D(n);
				} catch (e) {
					let t = xn(e);
					t ? (x(t.media_dirs ?? []), C(t.port ?? "")) : (x([]), C(""), T(B(e)));
				} finally {
					A.current = !1, v(M.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ Y("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ Y(bn, { html: d("configTitle", "这台电脑") }),
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
										onClick: (e) => re(n, e.currentTarget),
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
										onClick: () => te(n),
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
												value: l[n] || "",
												placeholder: "同名文件夹归入同一个媒体库",
												onInput: (e) => {
													let t = [...l];
													t[n] = e.currentTarget.value, u(t);
												}
											})] }),
											/* @__PURE__ */ Y("div", {
												class: "configsourcelabel",
												children: ["媒体库图标", /* @__PURE__ */ Y(wn, {
													libraryIcon: !0,
													label: `媒体库图标 ${n + 1}`,
													value: f[n] || "",
													onChange: (e) => {
														let t = [...f];
														t[n] = e, m(t);
													}
												})]
											}),
											/* @__PURE__ */ Y("div", {
												class: "configsourcelabel",
												children: ["媒体来源", /* @__PURE__ */ Y(wn, {
													label: `媒体来源 ${n + 1}`,
													value: a[n] || "local",
													onChange: (e) => {
														let t = [...a];
														t[n] = e, o(t);
													}
												})]
											}),
											e.windows === !1 ? /* @__PURE__ */ Y("label", { children: ["Windows 中的对应路径", /* @__PURE__ */ Y("input", {
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
						a.some((e) => e === "115" || e === "pikpak") ? /* @__PURE__ */ Y(hn, {}) : null,
						a.some((e) => e === "115" || e === "pikpak") ? e.mount_dependencies?.filter((e) => !e.available).map((e) => /* @__PURE__ */ Y("p", {
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
							value: h,
							"aria-invalid": S ? "true" : void 0,
							onInput: (e) => g(e.currentTarget.value)
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
							checked: _,
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
				w ? /* @__PURE__ */ Y(bn, { html: p(w, {
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
function En({ receipt: e, data: t, error: n }) {
	return n || !t ? /* @__PURE__ */ Y(bn, {
		class: "configpage",
		html: p(n || "没有读到配置", {
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
			t.startup ? /* @__PURE__ */ Y(dn, {
				startup: t.startup,
				receipt: e
			}) : null,
			/* @__PURE__ */ Y("h2", {
				class: "configgroup",
				children: "媒体"
			}),
			t.editable ? /* @__PURE__ */ Y(Tn, {
				data: t,
				receipt: e
			}) : /* @__PURE__ */ Y(bn, { html: p(t.notice, {
				variant: "secondary",
				label: "只读"
			}) }),
			/* @__PURE__ */ Y(Cn, { data: t }),
			t.peach_proxy || t.access ? /* @__PURE__ */ Y("h2", {
				class: "configgroup",
				children: "网络与访问"
			}) : null,
			t.peach_proxy ? /* @__PURE__ */ Y(cn, {
				initial: t.peach_proxy,
				receipt: e
			}) : null,
			t.access ? /* @__PURE__ */ Y(an, {
				initial: t.access,
				receipt: e
			}) : null,
			/* @__PURE__ */ Y("h2", {
				class: "configgroup",
				children: "更新与维护"
			}),
			t.updates ? /* @__PURE__ */ Y(sn, {
				initial: t.updates,
				initialJob: t.update_job
			}) : null,
			/* @__PURE__ */ Y(Sn, { facts: t.facts }),
			t.uninstall ? /* @__PURE__ */ Y(pn, { uninstall: t.uninstall }) : null
		]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var Dn = Symbol.for("preact-signals");
function On() {
	if (Z > 1) Z--;
	else {
		var e, t = !1;
		for ((function() {
			var e = In;
			for (In = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); Mn !== void 0;) {
			var n = Mn;
			for (Mn = void 0, Nn++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && Bn(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (Nn = 0, Z--, t) throw e;
	}
}
function kn(e) {
	if (Z > 0) return e();
	Fn = ++Pn, Z++;
	try {
		return e();
	} finally {
		On();
	}
}
var An, X = void 0;
function jn(e) {
	var t = X, n = An;
	X = void 0, An = void 0;
	try {
		return e();
	} finally {
		X = t, An = n;
	}
}
var Mn = void 0, Z = 0, Nn = 0, Pn = 0, Fn = 0, In = void 0, Ln = 0;
function Rn(e) {
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
Q.prototype.brand = Dn, Q.prototype.h = function() {
	return !0;
}, Q.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? jn(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, Q.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && jn(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, Q.prototype.subscribe = function(e) {
	var t = this;
	return Yn(function() {
		var n = t.value;
		jn(function() {
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
	return jn(function() {
		return e.value;
	});
}, Object.defineProperty(Q.prototype, "value", {
	get: function() {
		var e = Rn(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (Nn > 100) throw Error("Cycle detected");
			(function(e) {
				Z !== 0 && Nn === 0 && e.l !== Fn && (e.l = Fn, In = {
					S: e,
					v: e.v,
					i: e.i,
					o: In
				});
			})(this), this.v = e, this.i++, Ln++, Z++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				On();
			}
		}
	}
});
function zn(e, t) {
	return new Q(e, t);
}
function Bn(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function Vn(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function Hn(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function Un(e, t) {
	Q.call(this, void 0, t), this.x = e, this.s = void 0, this.g = Ln - 1, this.f = 4;
}
Un.prototype = new Q(), Un.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === Ln)) return !0;
	if (this.g = Ln, this.f |= 1, this.i > 0 && !Bn(this)) return this.f &= -2, !0;
	var e = X;
	try {
		Vn(this), X = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return X = e, Hn(this), this.f &= -2, !0;
}, Un.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	Q.prototype.S.call(this, e);
}, Un.prototype.U = function(e) {
	if (this.t !== void 0 && (Q.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, Un.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(Un.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = Rn(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function Wn(e, t) {
	return new Un(e, t);
}
function Gn(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		Z++;
		var n = X;
		X = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, Kn(e), t;
		} finally {
			X = n, On();
		}
	}
}
function Kn(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, Gn(e);
}
function qn(e) {
	if (X !== this) throw Error("Out-of-order effect");
	Hn(this), X = e, this.f &= -2, 8 & this.f && Kn(this), On();
}
function Jn(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, An && An.push(this);
}
Jn.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, Jn.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, Gn(this), Vn(this), Z++;
	var e = X;
	return X = this, qn.bind(this, e);
}, Jn.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = Mn, Mn = this);
}, Jn.prototype.d = function() {
	this.f |= 8, 1 & this.f || Kn(this);
}, Jn.prototype.dispose = function() {
	this.d();
};
function Yn(e, t) {
	var n = new Jn(e, t);
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
var Xn, Zn, Qn = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, $n = [];
Yn(function() {
	Xn = this.N;
})();
function er(e, t) {
	S[e] = t.bind(null, S[e] || function() {});
}
function tr(e) {
	if (Zn) {
		var t = Zn;
		Zn = void 0, t();
	}
	Zn = e && e.S();
}
function nr(e) {
	var t = this, n = e.data, r = ir(n);
	r.name = "ReactiveDom", r.value = n;
	var i = Jt(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = Wn(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = Wn(function() {
			return !Array.isArray(i.value) && !w(i.value);
		}), o = Yn(function() {
			if (this.N = sr, a.value) {
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
nr.displayName = "ReactiveTextNode", Object.defineProperties(Q.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: nr
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
}), er("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof Q && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), er("__r", function(e, t) {
	if (e(t), t.type !== I) {
		tr();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return Yn(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				Qn && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), tr(n);
	}
}), er("__e", function(e, t, n, r) {
	tr(), e(t, n, r);
}), er("diffed", function(e, t) {
	tr();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = rr(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function rr(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = zn(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: Yn(function() {
			this.N = sr;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
er("unmount", function(e, t) {
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
}), er("__h", function(e, t, n, r) {
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
function ir(e, t) {
	return Jt(function() {
		return zn(e, t);
	}, []);
}
var ar = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function or() {
	kn(function() {
		for (var e; e = $n.shift();) Xn.call(e);
	});
}
function sr() {
	$n.push(this) === 1 && (S.requestAnimationFrame || ar)(or);
}
//#endregion
//#region src/state/quality-goals.ts
var cr = "/api/quality-goals?limit=200", lr = {
	data: null,
	error: ""
}, ur = zn(lr), dr = 0, fr = Wn(() => ur.value);
Wn(() => ur.value.data?.total ?? null);
function pr() {
	dr += 1, ur.value = lr;
}
async function mr(e) {
	let t = dr += 1;
	try {
		let n = await V(cr, e);
		return t === dr && (ur.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === dr && (ur.value = {
			data: null,
			error: B(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var hr = (e, t) => mr(t), gr = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function _r({ openItem: t, javTitleHtml: n, javDisplayName: a, srcBadge: o }) {
	let { data: s, error: c } = fr.value;
	if (c) return /* @__PURE__ */ Y("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: p(c, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let l = s?.items ?? [];
	return l.length ? /* @__PURE__ */ Y("div", {
		class: "qualitylist",
		children: l.map((s) => /* @__PURE__ */ Y("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ Y("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${a(s)}`,
				onClick: () => t(s.id),
				children: /* @__PURE__ */ Y("img", {
					src: gr(s),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ Y("div", { children: [
				/* @__PURE__ */ Y("h3", { children: /* @__PURE__ */ Y("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => t(s.id),
					dangerouslySetInnerHTML: { __html: n(s) }
				}) }),
				/* @__PURE__ */ Y("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ Y("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: o(s.location, s.cost) }
						}),
						/* @__PURE__ */ Y("span", { children: e[s.location] ?? s.location }),
						/* @__PURE__ */ Y("span", { children: r(s.duration) }),
						/* @__PURE__ */ Y("span", { children: i(s.size ?? 0) })
					]
				}),
				s.reason ? /* @__PURE__ */ Y("p", { children: s.reason }) : null
			] })]
		}, s.id))
	}) : /* @__PURE__ */ Y("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: u("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/jobs.ts
async function vr(e) {
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
function yr(e) {
	let t = document.createElement("div");
	e.host.hidden = !0, t.dataset.followJob = "", t.setAttribute("aria-live", "polite"), e.host.prepend(t);
	let n = e.storageKey || "peach-follow-job", r = sessionStorage.getItem(n) || void 0, i = !1;
	vr({
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
var br = (e, t) => V("/api/scraping", t);
function xr({ value: e, onChange: t }) {
	let n = J(null), r = J(t);
	return r.current = t, q(() => {
		let t = n.current;
		t.innerHTML = g([["peach", "Peach 代理"], ["direct", "直接连接"]], e, { label: "连接方式" });
		let i = b(t.firstElementChild), a = () => r.current(i.value);
		return i.addEventListener("change", a), () => {
			i.disabled = !0, i.removeEventListener("change", a), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ Y("div", {
		ref: n,
		class: "scraping-network"
	});
}
function Sr({ source: e, toast: t }) {
	let [r, i] = G(e), [a, o] = G(e.network), [s, c] = G(""), [l, u] = G(""), [f, m] = G("paste"), [h, g] = G(""), [_, y] = G(!1), [b, x] = G(""), [S, C] = G([]), w = J(null), T = J(null);
	q(() => {
		T.current?.querySelectorAll("footer button").forEach((e) => v(e, _));
	}, [_]);
	let E = J(new AbortController());
	K(() => () => E.current.abort(), []);
	async function D(n) {
		if (!_) {
			y(!0), x(""), C([]);
			try {
				if (n === "check") {
					let t = await H("/api/scraping/check", { source: e.source }, "POST", E.current.signal);
					E.current.signal.aborted || C(t.results);
				} else {
					let r = await H("/api/scraping/settings", {
						source: e.source,
						network: a,
						cookie: s,
						cookies_text: l,
						revoke: n === "revoke"
					}, "POST", E.current.signal);
					E.current.signal.aborted || (i(r.saved), c(""), u(""), g(""), w.current && (w.current.value = ""), t(n === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
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
						children: [/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: d(`scraping-${e.source}`, e.label) } }), /* @__PURE__ */ Y("a", {
							class: "scraping-url externallink",
							href: e.login,
							target: "_blank",
							rel: "noopener noreferrer",
							children: [
								/* @__PURE__ */ Y("img", {
									src: n(e.login),
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
						children: ["连接方式", /* @__PURE__ */ Y(xr, {
							value: a,
							onChange: o
						})]
					}),
					a === "peach" && /* @__PURE__ */ Y("a", {
						class: "geist-text-link",
						href: "/configuration#peachProxy",
						children: "配置 Peach 代理"
					}),
					e.accepts_cookie && /* @__PURE__ */ Y(I, { children: [
						/* @__PURE__ */ Y("p", { children: r.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ Y("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ Y("label", { children: [/* @__PURE__ */ Y("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: f === t,
								onChange: () => {
									m(t), c(""), u(""), g("");
								}
							}), /* @__PURE__ */ Y("span", { children: n })] }, t))
						}),
						f === "paste" ? /* @__PURE__ */ Y("label", { children: ["Cookie", /* @__PURE__ */ Y("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: s,
							disabled: _,
							onInput: (e) => c(e.currentTarget.value)
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
					b && /* @__PURE__ */ Y("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: p(b, { variant: "error" }) }
					}),
					S.map((t) => /* @__PURE__ */ Y("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: p(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ Y("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					e.accepts_cookie && r.cookie_saved && /* @__PURE__ */ Y("button", {
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
function Cr({ data: e, error: t, toast: n }) {
	let [r, i] = G(""), [a, o] = G(!1), [s, c] = G(""), l = J(null);
	q(() => v(l.current, a), [a]);
	let u = J(new AbortController()), f = J(0);
	async function m(e = !1) {
		let t = ++f.current;
		await vr({
			read: (e) => V("/api/scraping/cover", e),
			active: () => !u.current.signal.aborted && t === f.current,
			render: (t) => {
				o(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && c(t.error || "采集未取得"), t.status === "complete" && !e && n(t.result || "封面采集完成");
			},
			disconnected: () => c("连接中断，正在重新读取后台进度")
		});
	}
	K(() => (m(!0), () => u.current.abort()), []);
	async function h() {
		if (!a) {
			f.current++, o(!0), c("");
			try {
				await H("/api/scraping/cover", { code: r }, "POST", u.current.signal), await m();
			} catch (e) {
				u.current.signal.aborted || (o(!1), c(B(e)));
			}
		}
	}
	return t ? /* @__PURE__ */ Y("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: p(t, { variant: "error" }) }
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
						/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: d("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ Y("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), h();
							},
							children: [/* @__PURE__ */ Y("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: r,
								disabled: a,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => i(e.currentTarget.value)
							}), /* @__PURE__ */ Y("button", {
								ref: l,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						s && /* @__PURE__ */ Y("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: p(s, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ Y(Sr, {
				source: e,
				toast: n
			}, e.source))
		]
	});
}
//#endregion
//#region src/islands/library-processing.tsx
var wr = (e, t) => V("/api/library-processing", t);
function Tr({ data: e, error: t, toast: n, onComplete: r, mode: i, monitor: a }) {
	let [o, s] = G(e || { status: "idle" }), [c, l] = G(t), [u, m] = G(!1), [g, _] = G(!1), y = J(new AbortController()), b = J(0), x = J(o.status), S = J(null), C = u || o.status === "running";
	q(() => v(S.current, C), [C]);
	async function w() {
		let e = ++b.current;
		await vr({
			read: (e) => V("/api/library-processing", e),
			active: () => !y.current.signal.aborted && b.current === e,
			keepWatching: i === "notice" || !!a,
			render: (e) => {
				s(e), l(""), e.status === "complete" && x.current === "running" && i !== "notice" && (_(!0), n("已完成扫描与资料采集")), x.current === "running" && (e.status === "complete" || e.status === "failed") && r?.(), x.current = e.status;
			},
			disconnected: () => l("连接中断，正在重新读取处理进度")
		});
	}
	K(() => ((o.status === "running" || i === "notice" || a) && w(), () => y.current.abort()), []);
	async function T() {
		if (!C) {
			m(!0), l(""), _(!1);
			try {
				let e = await H("/api/library-processing", {}, "POST", y.current.signal);
				if (y.current.signal.aborted) return;
				x.current = e.status, s(e), m(!1), await w();
			} catch (e) {
				y.current.signal.aborted || (l(B(e)), m(!1));
			}
		}
	}
	if (i === "notice") {
		if (!c && o.status !== "running" && o.status !== "failed") return null;
		let e = c || (o.status === "failed" ? "扫描与资料采集未完成" : `${o.stage || "正在整理馆藏"}${o.total ? ` · ${o.checked || 0} / ${o.total}` : ""}`);
		return /* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: h(e, {
			variant: o.status === "failed" ? "error" : c ? "warning" : "gray",
			href: "/data-cleanup#libraryProcessing",
			label: c || o.status === "failed" ? "查看并处理" : "查看进度",
			value: o.checked || 0,
			...o.status === "running" && o.total !== void 0 ? { max: o.total } : {}
		}) } });
	}
	return /* @__PURE__ */ Y(I, { children: [/* @__PURE__ */ Y("div", {
		class: "geist-fieldset-content library-processing",
		children: [
			/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: d("cleanupScrapingTitle", "扫描与采集") } }),
			/* @__PURE__ */ Y("p", { children: "扫描媒体文件夹，导入已有资料，采集缺失信息。" }),
			/* @__PURE__ */ Y("div", {
				"aria-live": "polite",
				children: [
					o.status === "running" && /* @__PURE__ */ Y(I, { children: [/* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: f(`${o.stage || "正在处理"}${o.total ? ` · ${o.checked || 0} / ${o.total}` : ""}`) } }), !!o.total && /* @__PURE__ */ Y("div", { dangerouslySetInnerHTML: { __html: Fe(`已处理 ${o.checked || 0} / ${o.total} 个视频`, o.checked || 0, o.total) } })] }),
					(c || o.status === "failed") && /* @__PURE__ */ Y("div", {
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
					o.status === "failed" && !!o.issues?.length && /* @__PURE__ */ Y("ul", { children: o.issues.slice(0, 20).map((e) => /* @__PURE__ */ Y("li", { children: [
						e.asset_id ? /* @__PURE__ */ Y("a", {
							href: `/item/${e.asset_id}`,
							children: "查看视频"
						}) : null,
						e.asset_id ? "：" : "",
						e.message
					] })) }),
					g && /* @__PURE__ */ Y("div", {
						class: "library-processing-result",
						dangerouslySetInnerHTML: { __html: p(`已扫描 ${o.scanned || 0} 个文件，识别 ${o.identified || 0} 个番号，整理 ${o.candidates || 0} 组资料候选。`, {
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
			!!o.candidates && /* @__PURE__ */ Y("a", {
				class: "geist-button",
				href: "/review",
				children: "复核资料"
			}),
			o.status !== "failed" && /* @__PURE__ */ Y("button", {
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
var Er = { "quality-goals": {
	refresh: mr,
	reset: pr
} }, Dr = () => Object.keys(Er);
async function Or(e) {
	let t = Er[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/review-evidence.ts
var kr = (e = "") => /^https?:\/\//i.test(e) ? e : "";
function Ar(e = "") {
	let n = kr(e) || (e.startsWith("/") && !e.startsWith("//") ? e : "");
	return `<div class="reviewimage" data-review-picture><span class="reviewimageempty"${n ? " hidden" : ""}>未取得来源图片</span>${n ? `<img src="${t(n)}" alt="来源候选图片" loading="lazy">` : ""}</div>`;
}
function jr(e) {
	let n = kr(e.profile_url), r = (e.preview_assets || []).slice(0, 6), i = Math.max(0, Number(e.video_count || e.videos || 0));
	return `<section class="reviewidentityevidence"><h5>候选身份：${t(e.babepedia_name || "未标注")}</h5>
    <div class="reviewevidenceactions">${n ? `<a class="geist-button externallink" href="${t(n)}" target="_blank" rel="noopener noreferrer">来源资料<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a>` : ""}
    <button type="button" class="geist-button" data-entity-kind="creator" data-entity-name="${t(e.creator || "")}">查看全部 ${i.toLocaleString()} 部作品</button></div>
    ${Ar(e.preview_url)}
    <p>通过后记录身份判断。</p>
    ${r.length ? `<h5>本地作品样本</h5><div class="reviewevidencesamples">${r.map((e) => `<div class="reviewevidencesample">
      <button class="geist-button" type="button" data-review-open-item="${e.id}"><span data-middle-truncate title="${t(e.name)}">${t(e.name)}</span></button>
      <button class="geist-button" type="button" data-review-reveal="${e.id}" aria-label="打开 ${t(e.name)} 的文件位置">文件位置</button>
    </div>`).join("")}</div>` : "<p>暂无本地作品样本，打开全部作品核对。</p>"}</section>`;
}
function Mr(e) {
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
var Nr = () => ({
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
function Pr(e) {
	let t = e?.querySelector(".reviewcontrols");
	if (!e || !t || t.offsetParent === null) return;
	let n = e.closest("main");
	n && e.style.setProperty("--review-edge", getComputedStyle(n).paddingLeft), e.style.setProperty("--review-controls-height", `${t.getBoundingClientRect().height}px`);
	for (let n of [t, ...e.querySelectorAll(".reviewgroupbar")]) {
		let e = parseFloat(getComputedStyle(n).top);
		n.classList.toggle("is-stuck", n.offsetParent !== null && window.scrollY > 0 && Number.isFinite(e) && Math.abs(n.getBoundingClientRect().top - e) <= 1);
	}
}
function Fr(e, t) {
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
function Ir(e, t) {
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
function Lr(e, t, n, r, i) {
	let a = e.anchor === null ? -1 : t.indexOf(e.anchor), o = t.indexOf(n);
	r && a >= 0 && o >= 0 ? t.slice(Math.min(a, o), Math.max(a, o) + 1).forEach((t) => e.selected.add(t)) : i ? e.selected.add(n) : e.selected.delete(n), e.anchor = n;
}
async function Rr(e, t, n, r) {
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
function zr(e) {
	return e.length ? [...new Set(e.flatMap((e) => e.candidates?.map((e) => e.source || "") || []))].filter((t) => t && e.every((e) => e.candidates?.filter((e) => e.source === t).length === 1)) : [];
}
function Br(e, t) {
	let n = e.querySelector(".reviewlist");
	if (!n || !t.rows.length || t.locked) return;
	let r = t.state, i = [...n.querySelectorAll("[data-review-key]")];
	t.category !== void 0 && r.category !== t.category && (r.category = t.category, r.filter = "", r.groupBy = "candidates", r.anchor = null);
	let a = Fr(t.rows, t.metadata);
	a.some((e) => e[0] === r.groupBy) || (r.groupBy = "candidates", r.filter = "");
	let o = Ir(t.rows, r.groupBy);
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
		r.selected.clear(), r.anchor = null, P();
	};
	A.onclick = () => {
		r.busy || (ee(), S.focus({ preventScroll: !0 }));
	}, S.onclick = () => {
		if (r.busy) return;
		let e = s(), t = l().length === e.length;
		e.forEach((e) => t ? r.selected.delete(e.dataset.reviewKey) : r.selected.add(e.dataset.reviewKey)), P();
	}, C.onclick = () => te("approved", C), w.onclick = () => te("rejected", w);
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
			t.forEach((t) => e ? r.selected.delete(t.dataset.reviewKey) : r.selected.add(t.dataset.reviewKey)), P();
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
				Lr(r, s().map((e) => e.dataset.reviewKey), t, e, n), P();
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
						a && (r.anchor === null && (r.anchor = t), Lr(r, i.map((e) => e.dataset.reviewKey), a.dataset.reviewKey, !0, !0), P(), a.querySelector(".reviewpickitem input")?.focus());
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
				n.checked && r.choices.set(t, n.value), P();
			});
		}
	}
	e.addEventListener("keydown", (t) => {
		r.busy || !e.contains(n) || (t.key === "Escape" && r.selected.size && (t.preventDefault(), t.stopPropagation(), ee()), (t.ctrlKey || t.metaKey) && t.key.toLowerCase() === "a" && !t.target.matches("textarea,input:not([type=\"checkbox\"]):not([type=\"radio\"])") && (t.preventDefault(), t.stopPropagation(), s().forEach((e) => r.selected.add(e.dataset.reviewKey)), P()));
	});
	let N = "";
	function P() {
		let e = l();
		S.textContent = e.length === s().length ? "清空当前选择" : r.filter ? "全选当前分类" : "全选本页", k.hidden = !e.length, T.textContent = `已选 ${e.length} 项`, C.disabled = !e.length || e.some((e) => !d(e)), w.disabled = !e.length;
		let n = zr(u());
		E.hidden = !t.metadata || !u().some((e) => (e.candidates?.length || 0) > 1);
		let i = e.length && !n.length ? "所选项目无共同来源" : "统一选择来源", a = JSON.stringify([i, n]);
		if (a !== N) {
			N = a, E.innerHTML = g([["", i], ...n.map((e) => [e, e])], "", { label: "统一选择来源" });
			let e = b(E.firstElementChild);
			e.disabled = !n.length, e.addEventListener("change", () => {
				if (!(r.busy || !zr(u()).includes(e.value))) {
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
	async function te(n, i) {
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
		let u = 0, d = await Rr(a, async (e) => {
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
	P(), Pr(e);
}
//#endregion
//#region src/native-image.ts
function Vr(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function Hr(e, t, n, r, i = 1) {
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
function Ur(e, t) {
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
function Wr(e) {
	let t = (e = "60%") => `<i class="skeleton" style="width:${e}"></i>`, n = () => `<div class="board-skeleton-row">${t("36%")}${t("24%")}</div>`, r = "";
	if (e === "/stats" || e === "/taste") r = `${e === "/taste" ? `<div class="board-skeleton-row">${t("26%")}${t("32%")}</div>` : ""}<div class="metricstrip board-skeleton-metrics">${Array.from({ length: 4 }, () => `<div class="tastesummary">${t()}<b class="skeleton"></b><small class="board-stat-footer">${t("48%")}</small></div>`).join("")}</div><div class="board-skeleton-chart"><div class="board-skeleton-ring skeleton"></div><div>${n().repeat(4)}</div></div><div class="board-skeleton-section">${t("32%")}${n().repeat(5)}</div>`;
	else if (e === "/follow-manage") r = `<div class="board-skeleton-section">${t("20%")}<div class="skeleton board-skeleton-input"></div>${t("72%")}</div><div class="board-skeleton-row">${t("24%")}${t("40%")}</div><div class="board-skeleton-section">${n().repeat(6)}</div><div class="board-skeleton-row">${t("30%")}${t("30%")}</div>`;
	else if (e === "/configuration") r = `<div class="board-skeleton-row">${t("16%").repeat(4)}</div><div class="board-skeleton-section">${t("24%")}${n().repeat(3)}<div class="skeleton board-skeleton-input"></div></div><div class="board-skeleton-section">${t("24%")}${n().repeat(2)}</div>`;
	else return "";
	return `<div class="board-page-skeleton" data-skeleton="board${e}" role="status" aria-label="正在读取页面"><div aria-hidden="true">${r}</div></div>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var Gr = [
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
function Kr() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function qr(e, t) {
	let n = new URLSearchParams();
	for (let t of Gr) e[t] && n.set(t, e[t]);
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
function Jr({ kind: e = "catalog", filtered: t = !1, jav: n = !1, configurable: r = !1, online: i = !1 } = {}) {
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
function Yr(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function Xr(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function Zr(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function Qr(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function $r(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function ei() {
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
function ti(e, t = !1, n = !1) {
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
var ni = "peach-taste-guide-dismissed";
function ri(e, t) {
	y(e, ".taste-history-guide", "taste-guide-collapse");
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(ni, "1"), n.remove();
	});
}
//#endregion
//#region src/resource-sync.ts
var $ = (e = 0) => Number(e).toLocaleString(), ii = {
	local: "本地磁盘",
	115: "115",
	pikpak: "PikPak"
};
function ai(e, t) {
	let n = e.cache || {
		files: 0,
		bytes: 0
	}, r = !!(e.missing || n.files);
	return `<div class="resourcepanel" data-geist-fieldset><div class="resourcesources">${(e.sources || []).map((e) => `<article>
    <div class="resourcesourcetitle"><b>${ii[e.location] || "媒体来源"}</b><span class="${e.online ? "online" : "offline"}">${e.online ? "可访问" : "离线，已跳过"}</span></div>
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
function oi(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function si(e) {
	return {
		javLayout: oi(e.javLayout),
		javImage: ci(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function ci(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function li(e, t) {
	return e.is_jav && e.code && e.has_cover && (ci(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function ui(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (ci(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.removeAttribute("style"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var di = {
	"library-processing": {
		load: wr,
		component: Tr
	},
	scraping: {
		load: br,
		component: Cr
	},
	"quality-goals": {
		load: hr,
		component: _r
	},
	configuration: {
		load: yn,
		component: En
	}
}, fi = () => Object.keys(di), pi = /* @__PURE__ */ new Map();
async function mi(e, t, n, r = {}) {
	let i = di[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	hi(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	pi.set(t, a);
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
	if (pi.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		pi.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	Oe(oe(i.component, s), t);
}
function hi(e) {
	let t = pi.get(e);
	t && (t.controller.abort(), pi.delete(e), t.painted && Oe(null, e));
}
//#endregion
export { ni as TASTE_GUIDE_KEY, Et as activityChartsHtml, Wr as boardPageSkeleton, je as boundedPreference, Jr as catalogEmptyHtml, qr as catalogSuggestions, ei as cleanupSkeletonHtml, Qr as cloudLocations, $r as cloudPreferenceLocations, Nr as createReviewSelection, bt as creatorSankeyHtml, Ie as distributionChart, Kr as emptyCatalogLayout, Ur as entitySkeletonHtml, yr as followJobProgress, jr as identityEvidenceHtml, Be as initBoardControls, fi as islandNames, li as javImageKind, Fe as jobProgressHtml, Vr as matchesFaceSource, mi as mountIsland, Ne as mountNumberSetting, Hr as nativeImageFit, ci as normalizeJavImage, oi as normalizeJavLayout, si as normalizeJavPreferences, ke as preferredDirection, Re as radarChart, Ct as radialCardHtml, Le as rankedChart, Or as refreshStore, ai as resourceScanHtml, Ar as reviewImageHtml, Yr as sidebarHasCatalogContent, kt as sidebarSectionHtml, Zr as sidebarTagCounts, Pe as statCardBody, Dr as storeNames, ze as syncBoardRange, ui as syncJavImages, Me as syncNumberSetting, Xr as syncSidebarSurface, ti as tasteHistoryGuideHtml, Mt as transitionTheme, hi as unmountIsland, Pr as updateReviewSticky, vr as watchJob, Dt as wireActivityCharts, xt as wireCreatorSankey, Ve as wireExpandableRanks, wt as wireRadialCards, Mr as wireReviewPictures, Br as wireReviewSelection, At as wireSidebarGroups, ri as wireTasteHistoryGuide };
