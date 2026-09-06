import { MEDIA_SOURCE_ICONS as e, emptyStateHtml as t, fieldsetTitle as n, noteHtml as r, selectFieldHtml as i, selectOptionIconHtml as a, setActionBusy as o, wireSelectField as s } from "/js/ui-components.js";
import { LOC as c, fmtDur as l, fmtSize as u } from "/js/core.js";
//#region node_modules/preact/dist/preact.module.js
var d, f, p, m, h, g, _, v, y, b, x, S, C, w, T, E = {}, D = [], O = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, k = Array.isArray;
function A(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function ee(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function te(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? d.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return j(e, o, r, i, null);
}
function j(e, t, n, r, i) {
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
		__v: i ?? ++p,
		__i: -1,
		__u: 0
	};
	return i == null && f.vnode != null && f.vnode(a), a;
}
function M(e) {
	return e.children;
}
function N(e, t) {
	this.props = e, this.context = t;
}
function P(e, t) {
	if (t == null) return e.__ ? P(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? P(e) : null;
}
function ne(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = A({}, t);
		a.__v = t.__v + 1, f.vnode && f.vnode(a), pe(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? P(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, he(r, a, i), t.__e = t.__ = null, a.__e != n && re(a);
	}
}
function re(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), re(e);
}
function ie(e) {
	(!e.__d && (e.__d = !0) && h.push(e) && !ae.__r++ || g != f.debounceRendering) && ((g = f.debounceRendering) || _)(ae);
}
function ae() {
	try {
		for (var e, t = 1; h.length;) h.length > t && h.sort(v), e = h.shift(), t = h.length, ne(e);
	} finally {
		h.length = ae.__r = 0;
	}
}
function oe(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || D, v = t.length;
	for (c = se(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || E, p.__i = d, g = pe(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && ve(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = ce(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function se(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = j(null, o, null, null, null) : k(o) ? o = e.__k[a] = j(M, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = j(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = le(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = P(s)), ye(s, s));
	return r;
}
function ce(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = ce(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = P(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function le(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function ue(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || O.test(t) ? n : n + "px";
}
function de(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || ue(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || ue(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(S, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[x] = r[x] : (n[x] = C, e.addEventListener(t, a ? T : w, a)) : e.removeEventListener(t, a ? T : w, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function fe(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[b] == null) t[b] = C++;
			else if (t[b] < n[x]) return;
			return n(f.event ? f.event(t) : t);
		}
	};
}
function pe(e, t, n, r, i, a, o, s, c, l) {
	var u, d, p, m, h, g, _, v, y, b, x, S, C, w, T, E, O = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (u = f.__b) && u(t);
	n: if (typeof O == "function") {
		d = o.length;
		try {
			if (y = t.props, b = O.prototype && O.prototype.render, x = (u = O.contextType) && r[u.__c], S = u ? x ? x.props.value : u.__ : r, n.__c ? v = (p = t.__c = n.__c).__ = p.__E : (b ? t.__c = p = new O(y, S) : (t.__c = p = new N(y, S), p.constructor = O, p.render = be), x && x.sub(p), p.state || (p.state = {}), p.__n = r, m = p.__d = !0, p.__h = [], p._sb = []), b && p.__s == null && (p.__s = p.state), b && O.getDerivedStateFromProps != null && (p.__s == p.state && (p.__s = A({}, p.__s)), A(p.__s, O.getDerivedStateFromProps(y, p.__s))), h = p.props, g = p.state, p.__v = t, m) b && O.getDerivedStateFromProps == null && p.componentWillMount != null && p.componentWillMount(), b && p.componentDidMount != null && p.__h.push(p.componentDidMount);
			else {
				if (b && O.getDerivedStateFromProps == null && y !== h && p.componentWillReceiveProps != null && p.componentWillReceiveProps(y, S), t.__v == n.__v || !p.__e && p.shouldComponentUpdate != null && !1 === p.shouldComponentUpdate(y, p.__s, S)) {
					t.__v != n.__v && (p.props = y, p.state = p.__s, p.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), D.push.apply(p.__h, p._sb), p._sb = [], p.__h.length && o.push(p), s = P(n);
					break n;
				}
				p.componentWillUpdate != null && p.componentWillUpdate(y, p.__s, S), b && p.componentDidUpdate != null && p.__h.push(function() {
					p.componentDidUpdate(h, g, _);
				});
			}
			if (p.context = S, p.props = y, p.__P = e, p.__e = !1, C = f.__r, w = 0, b) p.state = p.__s, p.__d = !1, C && C(t), u = p.render(p.props, p.state, p.context), D.push.apply(p.__h, p._sb), p._sb = [];
			else do
				p.__d = !1, C && C(t), u = p.render(p.props, p.state, p.context), p.state = p.__s;
			while (p.__d && ++w < 25);
			p.state = p.__s, p.getChildContext != null && (r = A(A({}, r), p.getChildContext())), b && !m && p.getSnapshotBeforeUpdate != null && (_ = p.getSnapshotBeforeUpdate(h, g)), T = u != null && u.type === M && u.key == null ? ge(u.props.children) : u, s = oe(e, k(T) ? T : [T], t, n, r, i, a, o, s, c, l), p.base = t.__e, t.__u &= -161, p.__h.length && o.push(p), v && (p.__E = p.__ = null);
		} catch (e) {
			if (o.length = d, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (E = a.length; E--;) ee(a[E]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || me(t), f.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = _e(n.__e, t, n, r, i, a, o, c, l);
	return (u = f.diffed) && u(t), 128 & t.__u ? void 0 : s;
}
function me(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(me));
}
function he(e, t, n) {
	for (var r = 0; r < n.length; r++) ve(n[r], n[++r], n[++r]);
	f.__c && f.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			f.__e(e, t.__v);
		}
	});
}
function ge(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : k(e) ? e.map(ge) : e.constructor === void 0 ? A({}, e) : null;
}
function _e(e, t, n, r, i, a, o, s, c) {
	var l, u, p, m, h, g, _, v = n.props || E, y = t.props, b = t.type;
	if (b == "svg" ? i = "http://www.w3.org/2000/svg" : b == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (l = 0; l < a.length; l++) if ((h = a[l]) && "setAttribute" in h == !!b && (b ? h.localName == b : h.nodeType == 3)) {
			e = h, a[l] = null;
			break;
		}
	}
	if (e == null) {
		if (b == null) return document.createTextNode(y);
		e = document.createElementNS(i, b, y.is && y), s &&= (f.__m && f.__m(t, a), !1), a = null;
	}
	if (b == null) v === y || s && e.data == y || (e.data = y);
	else {
		if (a = b == "textarea" && y.defaultValue != null ? null : a && d.call(e.childNodes), !s && a != null) for (v = {}, l = 0; l < e.attributes.length; l++) v[(h = e.attributes[l]).name] = h.value;
		for (l in v) h = v[l], l == "dangerouslySetInnerHTML" ? p = h : l == "children" || l in y || l == "value" && "defaultValue" in y || l == "checked" && "defaultChecked" in y || de(e, l, null, h, i);
		for (l in y) h = y[l], l == "children" ? m = h : l == "dangerouslySetInnerHTML" ? u = h : l == "value" ? g = h : l == "checked" ? _ = h : s && typeof h != "function" || v[l] === h || de(e, l, h, v[l], i);
		if (u) s || p && (u.__html == p.__html || u.__html == e.innerHTML) || (e.innerHTML = u.__html), t.__k = [];
		else if (p && (e.innerHTML = ""), oe(t.type == "template" ? e.content : e, k(m) ? m : [m], t, n, r, b == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && P(n, 0), s, c), a != null) for (l = a.length; l--;) ee(a[l]);
		s && b != "textarea" || (l = "value", b == "progress" && g == null ? e.removeAttribute("value") : g != null && (g !== e[l] || b == "progress" && !g || b == "option" && g != v[l]) && de(e, l, g, v[l], i), l = "checked", _ != null && _ != e[l] && de(e, l, _, v[l], i));
	}
	return e;
}
function ve(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		f.__e(e, n);
	}
}
function ye(e, t, n) {
	var r, i;
	if (f.unmount && f.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || ve(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			f.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && ye(r[i], t, n || typeof e.type != "function");
	n || ee(e.__e), e.__c = e.__ = e.__e = void 0;
}
function be(e, t, n) {
	return this.constructor(e, n);
}
function xe(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), f.__ && f.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], pe(t, e = (!r && n || t).__k = te(M, null, [e]), i || E, E, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? d.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), he(a, e, o), e.props.children = null;
}
d = D.slice, f = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, p = 0, m = function(e) {
	return e != null && e.constructor === void 0;
}, N.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = A({}, this.state);
	typeof e == "function" && (e = e(A({}, n), this.props)), e && A(n, e), e != null && this.__v && (t && this._sb.push(t), ie(this));
}, N.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), ie(this));
}, N.prototype.render = M, h = [], _ = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, v = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, ae.__r = 0, y = Math.random().toString(8), b = "__d" + y, x = "__a" + y, S = /(PointerCapture)$|Capture$/i, C = 0, w = fe(!1), T = fe(!0);
//#endregion
//#region src/api.ts
var Se = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(e), this.name = "ApiError", this.status = t, this.body = n;
	}
}, Ce = (e) => {
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
}, F = (e) => e instanceof Error ? e.message : String(e);
async function I(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new Se(Ce(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function L(e, t, n = "POST", r) {
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
	if (!i.ok) throw new Se(Ce(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var R, z, we, Te, Ee = 0, De = [], B = f, Oe = B.__b, ke = B.__r, Ae = B.diffed, je = B.__c, Me = B.unmount, Ne = B.__;
function Pe(e, t) {
	B.__h && B.__h(z, e, Ee || t), Ee = 0;
	var n = z.__H || (z.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function V(e) {
	return Ee = 1, Fe(We, e);
}
function Fe(e, t, n) {
	var r = Pe(R++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : We(void 0, t), function(e) {
		var t = r.__N ? r.__N[0] : r.__[0], n = r.t(t, e);
		t !== n && (r.__N = [n, r.__[1]], r.__c.setState({}));
	}], r.__c = z, !z.__f)) {
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
		z.__f = !0;
		var a = z.shouldComponentUpdate, o = z.componentWillUpdate;
		z.componentWillUpdate = function(e, t, n) {
			if (this.__e) {
				var r = a;
				a = void 0, i(e, t, n), a = r;
			}
			o && o.call(this, e, t, n);
		}, z.shouldComponentUpdate = i;
	}
	return r.__N || r.__;
}
function Ie(e, t) {
	var n = Pe(R++, 3);
	!B.__s && Ue(n.__H, t) && (n.__ = e, n.u = t, z.__H.__h.push(n));
}
function H(e, t) {
	var n = Pe(R++, 4);
	!B.__s && Ue(n.__H, t) && (n.__ = e, n.u = t, z.__h.push(n));
}
function U(e) {
	return Ee = 5, Le(function() {
		return { current: e };
	}, []);
}
function Le(e, t) {
	var n = Pe(R++, 7);
	return Ue(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function Re() {
	for (var e; e = De.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(Ve), t.__h.some(He), t.__h = [];
		} catch (n) {
			t.__h = [], B.__e(n, e.__v);
		}
	}
}
B.__b = function(e) {
	z = null, Oe && Oe(e);
}, B.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), Ne && Ne(e, t);
}, B.__r = function(e) {
	ke && ke(e), R = 0;
	var t = (z = e.__c).__H;
	t && (we === z ? (t.__h = [], z.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(Ve), t.__h.some(He), t.__h = [], R = 0)), we = z;
}, B.diffed = function(e) {
	Ae && Ae(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (De.push(t) !== 1 && Te === B.requestAnimationFrame || ((Te = B.requestAnimationFrame) || Be)(Re)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), we = z = null;
}, B.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(Ve), e.__h = e.__h.filter(function(e) {
				return !e.__ || He(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], B.__e(n, e.__v);
		}
	}), je && je(e, t);
}, B.unmount = function(e) {
	Me && Me(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			Ve(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && B.__e(t, n.__v));
};
var ze = typeof requestAnimationFrame == "function";
function Be(e) {
	var t, n = function() {
		clearTimeout(r), ze && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	ze && (t = requestAnimationFrame(n));
}
function Ve(e) {
	var t = z, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), z = t;
}
function He(e) {
	var t = z;
	e.__c = e.__(), z = t;
}
function Ue(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function We(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var Ge = 0;
Array.isArray;
function W(e, t, n, r, i, a) {
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
		__v: --Ge,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (o = e.defaultProps)) for (s in o) c[s] === void 0 && (c[s] = o[s]);
	return f.vnode && f.vnode(l), l;
}
//#endregion
//#region src/islands/access-settings.tsx
function Ke({ id: e, label: t, value: n, onInput: r, error: i, help: a, current: o = !1 }) {
	return /* @__PURE__ */ W("div", {
		class: "configfield",
		children: [
			/* @__PURE__ */ W("label", {
				for: e,
				children: t
			}),
			/* @__PURE__ */ W("input", {
				id: e,
				class: "geist-input",
				type: "password",
				autoComplete: o ? "current-password" : "new-password",
				maxLength: 256,
				value: n,
				onInput: (e) => r(e.currentTarget.value),
				required: !0,
				"aria-invalid": !!i,
				"aria-describedby": i || a ? `${e}-hint` : void 0
			}),
			i || a ? /* @__PURE__ */ W("p", {
				id: `${e}-hint`,
				class: i ? "configbad" : "confighelp",
				role: i ? "alert" : void 0,
				children: i || a
			}) : null
		]
	});
}
function qe({ initial: e, receipt: t }) {
	let [r, i] = V(e), [a, s] = V(""), [c, l] = V(""), [u, d] = V(""), [f, p] = V(!1), [m, h] = V(""), [g, _] = V({}), v = U(null), y = U(!1), b = U(null);
	return /* @__PURE__ */ W("form", {
		class: "configfieldset",
		onSubmit: async (e) => {
			if (e.preventDefault(), y.current) return;
			h("");
			let n = {};
			if (r.mode === "password" && !a && (n.current_password = "请输入当前访问密码"), f || ((c.length < 8 || c.length > 256) && (n.password = "访问密码需为 8–256 个字符"), c !== u && (n.confirmation = "两次输入的密码不一致")), _(n), Object.keys(n).length) {
				requestAnimationFrame(() => v.current?.querySelector("[aria-invalid=\"true\"]")?.focus());
				return;
			}
			y.current = !0, o(b.current, !0);
			try {
				let e = await L("/api/configuration/access", {
					revision: r.revision,
					action: f ? "disable" : "set",
					confirm_disable: f,
					current_password: a,
					password: f ? "" : c,
					confirmation: f ? "" : u
				});
				i(e), s(""), l(""), d(""), p(!1), _({}), t(e.mode === "open" ? "已关闭访问密码" : "已保存访问密码");
			} catch (e) {
				let t = e instanceof Se ? e.body : null, n = t?.errors || t?.detail?.errors;
				n ? _(n) : h(F(e));
			} finally {
				y.current = !1, o(b.current, !1);
			}
		},
		"aria-labelledby": "accessTitle",
		noValidate: !0,
		ref: v,
		children: [/* @__PURE__ */ W("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ W("div", { dangerouslySetInnerHTML: { __html: n("accessTitle", "访问密码") } }),
				/* @__PURE__ */ W("p", {
					class: "confighelp",
					children: r.mode === "open" ? "未设置密码，能连接到 Peach 的设备可直接访问。" : r.mode === "legacy" ? "当前使用系统生成的访问口令。你可以设置自己的密码，或关闭登录要求。" : r.mode === "locked" ? "访问设置无法读取，请在本机检查配置文件。" : "已设置密码。新设备需要登录，保持登录时间在登录页选择。"
				}),
				r.mode === "password" ? /* @__PURE__ */ W(Ke, {
					id: "access-current",
					label: "当前访问密码",
					value: a,
					onInput: s,
					error: g.current_password,
					current: !0
				}) : null,
				!f && r.mode !== "locked" ? /* @__PURE__ */ W(M, { children: [/* @__PURE__ */ W(Ke, {
					id: "access-password",
					label: r.mode === "password" ? "新访问密码" : "设置访问密码",
					value: c,
					onInput: l,
					error: g.password,
					help: "至少 8 个字符。保存后其他设备需要重新登录。"
				}), /* @__PURE__ */ W(Ke, {
					id: "access-confirm",
					label: "确认访问密码",
					value: u,
					onInput: d,
					error: g.confirmation
				})] }) : null,
				r.mode === "password" || r.mode === "legacy" ? /* @__PURE__ */ W("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ W("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ W("input", {
							type: "checkbox",
							checked: f,
							onChange: (e) => p(e.currentTarget.checked)
						}), /* @__PURE__ */ W("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ W("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ W("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ W("span", { children: "关闭访问密码，允许能连接到 Peach 的设备直接访问" })]
				}) : null,
				m ? /* @__PURE__ */ W("p", {
					class: "configbad",
					role: "alert",
					children: m
				}) : null
			]
		}), r.mode === "locked" ? null : /* @__PURE__ */ W("div", {
			class: "geist-fieldset-footer",
			children: [/* @__PURE__ */ W("p", { children: "保存后立即生效。" }), /* @__PURE__ */ W("button", {
				class: "geist-button",
				type: "submit",
				ref: b,
				children: f ? "关闭访问密码" : "保存访问密码"
			})]
		})]
	});
}
//#endregion
//#region src/islands/configuration.tsx
var Je = "/api/configuration", Ye = "/api/pick-folder", Xe = 8e3, Ze = (e, t) => I(Je, t), G = ({ html: e, class: t }) => /* @__PURE__ */ W("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), Qe = (e) => !(e instanceof Se) || e.status !== 400 ? null : e.body?.errors ?? null;
function $e({ facts: e }) {
	return /* @__PURE__ */ W("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ W("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ W(G, { html: n("configFactsTitle", "运行信息") }), /* @__PURE__ */ W("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ W(M, { children: [/* @__PURE__ */ W("dt", { children: e.term }), /* @__PURE__ */ W("dd", { children: [e.value, e.download_url ? /* @__PURE__ */ W("span", {
					class: "confighelp",
					children: [" ", /* @__PURE__ */ W("a", {
						href: e.download_url,
						target: "_blank",
						rel: "noreferrer",
						children: [e.download_label, /* @__PURE__ */ W("svg", {
							"aria-hidden": "true",
							viewBox: "0 0 24 24",
							children: /* @__PURE__ */ W("use", { href: "#i-external-link" })
						})]
					})]
				}) : null] })] }))
			})]
		})
	});
}
function et({ data: t }) {
	let [r, i] = V(t.media_sources), [s, c] = V(""), l = U(null);
	Ie(() => () => l.current?.abort(), []);
	let u = async (e) => {
		if (l.current) return;
		let t = new AbortController();
		l.current = t, o(e, !0), c("");
		try {
			let e = await I(Je, t.signal);
			t.signal.aborted || i(e.media_sources);
		} catch (e) {
			t.signal.aborted || c(F(e));
		} finally {
			l.current = null, o(e, !1);
		}
	};
	return r ? /* @__PURE__ */ W("section", {
		class: "configfieldset",
		"aria-labelledby": "configMountsTitle",
		children: /* @__PURE__ */ W("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ W(G, { html: n("configMountsTitle", "挂载状态") }),
				/* @__PURE__ */ W("dl", {
					class: "configfacts",
					children: r.map((t) => /* @__PURE__ */ W(M, { children: [/* @__PURE__ */ W("dt", { children: [/* @__PURE__ */ W("span", {
						"aria-hidden": "true",
						dangerouslySetInnerHTML: { __html: a(e[t.location]) }
					}), {
						local: "本地磁盘",
						115: "CloudDrive · 115",
						pikpak: "CloudDrive · PikPak"
					}[t.location] || t.location] }), /* @__PURE__ */ W("dd", { children: [
						t.path || "未配置挂载点",
						" ",
						/* @__PURE__ */ W("span", {
							class: `configstatus ${t.online === !0 ? "online" : t.online === !1 ? "offline" : "unknown"}`,
							children: t.online === !0 ? "在线" : t.online === !1 ? "离线" : "未检测"
						})
					] })] }))
				}),
				s ? /* @__PURE__ */ W("p", {
					class: "configbad",
					role: "alert",
					children: s
				}) : null,
				/* @__PURE__ */ W("button", {
					type: "button",
					class: "geist-button",
					onClick: (e) => u(e.currentTarget),
					children: "刷新挂载状态"
				})
			]
		})
	}) : null;
}
function tt({ value: t, label: n, onChange: r }) {
	let a = U(null), o = U(null), c = U(r);
	return c.current = r, H(() => {
		let r = a.current;
		r.innerHTML = i([
			["local", "本地磁盘"],
			["115", "CloudDrive · 115"],
			["pikpak", "CloudDrive · PikPak"]
		].map(([t, n]) => [
			t,
			n,
			e[t]
		]), t, { label: n });
		let l = s(r.firstElementChild);
		o.current = l;
		let u = () => c.current(l.value);
		return l.addEventListener("change", u), () => {
			o.current = null, l.disabled = !0, l.removeEventListener("change", u), r.replaceChildren();
		};
	}, [n]), H(() => {
		o.current && (o.current.value = t);
	}, [t]), /* @__PURE__ */ W("div", {
		ref: a,
		class: "configsourcecontrol"
	});
}
function nt({ data: e, receipt: t }) {
	let i = e.media_sources?.filter((e) => [
		"local",
		"115",
		"pikpak"
	].includes(e.location)), [a, s] = V(i?.length ? i.map((e) => e.path) : e.media_dirs.length ? e.media_dirs : [""]), [c, l] = V(i?.map((e) => e.location) ?? []), [u, d] = V(i?.map((e) => e.root) ?? []), [f, p] = V(String(e.port)), [m, h] = V(!1), [g, _] = V([]), [v, y] = V(""), [b, x] = V(""), [S, C] = V(null), [w, T] = V(null), E = U(!1), D = U(e.revision), O = U([]), k = U(null);
	H(() => {
		w !== null && (O.current[w]?.focus(), T(null));
	}, [w]), Ie(() => {
		if (!S) return;
		let e = setTimeout(() => location.assign(S.url), Xe);
		return () => clearTimeout(e);
	}, [S]);
	let A = (e, t) => {
		s((n) => n.map((n, r) => r === e ? t : n));
	}, ee = () => {
		T(a.length), s((e) => [...e, ""]);
	}, te = (e) => {
		l((t) => t.filter((t, n) => n !== e)), d((t) => t.filter((t, n) => n !== e)), s((t) => t.filter((t, n) => n !== e)), _((t) => t.filter((t, n) => n !== e));
	}, j = (e, t) => {
		_((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, M = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			o(t, !0);
			try {
				let { path: t } = await L(Ye, { initial: a[e] ?? "" });
				t && (A(e, t), j(e, ""));
			} catch (t) {
				j(e, F(t));
			} finally {
				o(t, !1);
			}
		}
	};
	return S ? /* @__PURE__ */ W("div", {
		class: "configsaved",
		role: "status",
		children: [/* @__PURE__ */ W(G, { html: r("配置已保存，Peach 正在重新启动。", {
			variant: "success",
			label: "已保存"
		}) }), /* @__PURE__ */ W("p", {
			class: "confighelp",
			children: [
				"几秒后自动打开新地址；没跳转就点 ",
				/* @__PURE__ */ W("a", {
					href: S.url,
					children: "进入馆藏"
				}),
				"。"
			]
		})]
	}) : /* @__PURE__ */ W("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configTitle",
		onSubmit: async (n) => {
			if (n.preventDefault(), !E.current) {
				E.current = !0, o(k.current, !0), x("");
				try {
					let n = await L(Je, {
						revision: D.current,
						media_dirs: a,
						...e.media_sources ? { media_sources: a.map((e, t) => ({
							path: e,
							location: c[t] || "local",
							root: u[t] || ""
						})) } : {},
						port: f,
						scan_now: m
					});
					D.current = n.revision, _([]), y(""), t("已保存配置"), C(n);
				} catch (e) {
					let t = Qe(e);
					t ? (_(t.media_dirs ?? []), y(t.port ?? "")) : (_([]), y(""), x(F(e)));
				} finally {
					E.current = !1, o(k.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ W("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ W(G, { html: n("configTitle", "这台电脑") }),
				/* @__PURE__ */ W("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ W("span", {
							class: "configlabel",
							id: "configDirsLabel",
							children: "媒体文件夹"
						}),
						/* @__PURE__ */ W("div", {
							class: "configdirs",
							role: "group",
							"aria-labelledby": "configDirsLabel",
							children: a.map((t, n) => /* @__PURE__ */ W("div", {
								class: "configdir",
								children: [
									/* @__PURE__ */ W("span", {
										class: "configpathlabel",
										children: ["本机文件夹 ", n + 1]
									}),
									/* @__PURE__ */ W("input", {
										class: "geist-input",
										type: "text",
										value: t,
										"aria-label": `媒体文件夹 ${n + 1}`,
										"aria-invalid": g[n] ? "true" : void 0,
										onInput: (e) => A(n, e.currentTarget.value),
										ref: (e) => {
											O.current[n] = e;
										}
									}),
									/* @__PURE__ */ W("button", {
										type: "button",
										class: "geist-button configpick",
										"aria-label": "选择文件夹",
										onClick: (e) => M(n, e.currentTarget),
										children: /* @__PURE__ */ W("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ W("use", { href: "#i-folder-search" })
										})
									}),
									a.length > 1 ? /* @__PURE__ */ W("button", {
										type: "button",
										class: "geist-button configrm",
										"aria-label": "移除这个文件夹",
										onClick: () => te(n),
										children: /* @__PURE__ */ W("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ W("use", { href: "#i-x" })
										})
									}) : null,
									/* @__PURE__ */ W("div", {
										class: "configsource",
										children: [/* @__PURE__ */ W("div", {
											class: "configsourcelabel",
											children: ["媒体来源", /* @__PURE__ */ W(tt, {
												label: `媒体来源 ${n + 1}`,
												value: c[n] || "local",
												onChange: (e) => {
													let t = [...c];
													t[n] = e, l(t);
												}
											})]
										}), e.windows === !1 ? /* @__PURE__ */ W("label", { children: ["Windows 中的对应路径", /* @__PURE__ */ W("input", {
											class: "geist-input",
											"aria-label": `Windows 中的对应路径 ${n + 1}`,
											value: u[n] || "",
											placeholder: "例如 B:\\\\",
											onInput: (e) => {
												let t = [...u];
												t[n] = e.currentTarget.value, d(t);
											}
										})] }) : null]
									}),
									g[n] ? /* @__PURE__ */ W("p", {
										class: "configbad",
										role: "alert",
										children: g[n]
									}) : null
								]
							}, n))
						}),
						/* @__PURE__ */ W("button", {
							type: "button",
							class: "geist-button configadd",
							onClick: ee,
							children: "添加文件夹"
						}),
						c.some((e) => e === "115" || e === "pikpak") ? /* @__PURE__ */ W("p", {
							class: "confighelp",
							children: ["先在 CloudDrive 登录网盘并完成挂载。", /* @__PURE__ */ W("a", {
								href: "https://www.clouddrive2.com/help.html",
								target: "_blank",
								rel: "noreferrer",
								children: ["挂载帮助", /* @__PURE__ */ W("svg", {
									"aria-hidden": "true",
									viewBox: "0 0 24 24",
									children: /* @__PURE__ */ W("use", { href: "#i-external-link" })
								})]
							})]
						}) : null,
						c.some((e) => e === "115" || e === "pikpak") ? e.mount_dependencies?.filter((e) => !e.available).map((e) => /* @__PURE__ */ W("p", {
							class: "confighelp",
							children: [
								"未检测到 ",
								e.name,
								"。",
								/* @__PURE__ */ W("a", {
									href: e.download_url,
									target: "_blank",
									rel: "noreferrer",
									children: [
										"下载 ",
										e.name,
										/* @__PURE__ */ W("svg", {
											"aria-hidden": "true",
											viewBox: "0 0 24 24",
											children: /* @__PURE__ */ W("use", { href: "#i-external-link" })
										})
									]
								})
							]
						})) : null,
						e.windows === !1 ? /* @__PURE__ */ W("p", {
							class: "confighelp",
							children: "本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\\ 对应本机挂载文件夹。"
						}) : null
					]
				}),
				e.port_editable === !1 ? null : /* @__PURE__ */ W("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ W("label", {
							for: "configPort",
							children: "本机访问端口"
						}),
						/* @__PURE__ */ W("input", {
							id: "configPort",
							class: "geist-input",
							type: "text",
							inputMode: "numeric",
							value: f,
							"aria-invalid": v ? "true" : void 0,
							onInput: (e) => p(e.currentTarget.value)
						}),
						v ? /* @__PURE__ */ W("p", {
							class: "configbad",
							role: "alert",
							children: v
						}) : null,
						/* @__PURE__ */ W("p", {
							class: "confighelp",
							children: "浏览器地址里冒号后面的数字，一般不用改。"
						})
					]
				}),
				/* @__PURE__ */ W("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ W("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ W("input", {
							type: "checkbox",
							checked: m,
							onChange: (e) => h(e.currentTarget.checked)
						}), /* @__PURE__ */ W("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ W("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ W("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ W("span", { children: "保存后扫描媒体文件夹" })]
				}),
				b ? /* @__PURE__ */ W(G, { html: r(b, {
					variant: "error",
					label: "没有保存"
				}) }) : null
			]
		}), /* @__PURE__ */ W("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [/* @__PURE__ */ W("p", { children: e.port_editable === !1 ? "保存后 Peach 会重新载入配置。" : "保存后 Peach 会重新启动，端口改了就用新地址打开。" }), /* @__PURE__ */ W("button", {
				type: "submit",
				class: "geist-button primary",
				ref: k,
				children: "保存配置"
			})]
		})]
	});
}
function rt({ receipt: e, data: t, error: n }) {
	return n || !t ? /* @__PURE__ */ W(G, {
		class: "configpage",
		html: r(n || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		})
	}) : /* @__PURE__ */ W("div", {
		class: "configpage",
		children: [
			t.editable ? /* @__PURE__ */ W(nt, {
				data: t,
				receipt: e
			}) : /* @__PURE__ */ W(G, { html: r(t.notice, {
				variant: "secondary",
				label: "只读"
			}) }),
			t.access ? /* @__PURE__ */ W(qe, {
				initial: t.access,
				receipt: e
			}) : null,
			/* @__PURE__ */ W($e, { facts: t.facts }),
			/* @__PURE__ */ W(et, { data: t })
		]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var it = Symbol.for("preact-signals");
function at() {
	if (q > 1) q--;
	else {
		var e, t = !1;
		for ((function() {
			var e = pt;
			for (pt = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); lt !== void 0;) {
			var n = lt;
			for (lt = void 0, ut++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && _t(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (ut = 0, q--, t) throw e;
	}
}
function ot(e) {
	if (q > 0) return e();
	ft = ++dt, q++;
	try {
		return e();
	} finally {
		at();
	}
}
var st, K = void 0;
function ct(e) {
	var t = K, n = st;
	K = void 0, st = void 0;
	try {
		return e();
	} finally {
		K = t, st = n;
	}
}
var lt = void 0, q = 0, ut = 0, dt = 0, ft = 0, pt = void 0, mt = 0;
function ht(e) {
	if (K !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== K) return t = {
			i: 0,
			S: e,
			p: K.s,
			n: void 0,
			t: K,
			e: void 0,
			x: void 0,
			r: t
		}, K.s !== void 0 && (K.s.n = t), K.s = t, e.n = t, 32 & K.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = K.s, t.n = void 0, K.s.n = t, K.s = t), t;
	}
}
function J(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
J.prototype.brand = it, J.prototype.h = function() {
	return !0;
}, J.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? ct(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, J.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && ct(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, J.prototype.subscribe = function(e) {
	var t = this;
	return Z(function() {
		var n = t.value;
		ct(function() {
			return e(n);
		});
	}, { name: "sub" });
}, J.prototype.valueOf = function() {
	return this.value;
}, J.prototype.toString = function() {
	return this.value + "";
}, J.prototype.toJSON = function() {
	return this.value;
}, J.prototype.peek = function() {
	var e = this;
	return ct(function() {
		return e.value;
	});
}, Object.defineProperty(J.prototype, "value", {
	get: function() {
		var e = ht(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (ut > 100) throw Error("Cycle detected");
			(function(e) {
				q !== 0 && ut === 0 && e.l !== ft && (e.l = ft, pt = {
					S: e,
					v: e.v,
					i: e.i,
					o: pt
				});
			})(this), this.v = e, this.i++, mt++, q++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				at();
			}
		}
	}
});
function gt(e, t) {
	return new J(e, t);
}
function _t(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function vt(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function yt(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function Y(e, t) {
	J.call(this, void 0, t), this.x = e, this.s = void 0, this.g = mt - 1, this.f = 4;
}
Y.prototype = new J(), Y.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === mt)) return !0;
	if (this.g = mt, this.f |= 1, this.i > 0 && !_t(this)) return this.f &= -2, !0;
	var e = K;
	try {
		vt(this), K = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return K = e, yt(this), this.f &= -2, !0;
}, Y.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	J.prototype.S.call(this, e);
}, Y.prototype.U = function(e) {
	if (this.t !== void 0 && (J.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, Y.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(Y.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = ht(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function bt(e, t) {
	return new Y(e, t);
}
function xt(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		q++;
		var n = K;
		K = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, St(e), t;
		} finally {
			K = n, at();
		}
	}
}
function St(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, xt(e);
}
function Ct(e) {
	if (K !== this) throw Error("Out-of-order effect");
	yt(this), K = e, this.f &= -2, 8 & this.f && St(this), at();
}
function X(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, st && st.push(this);
}
X.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, X.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, xt(this), vt(this), q++;
	var e = K;
	return K = this, Ct.bind(this, e);
}, X.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = lt, lt = this);
}, X.prototype.d = function() {
	this.f |= 8, 1 & this.f || St(this);
}, X.prototype.dispose = function() {
	this.d();
};
function Z(e, t) {
	var n = new X(e, t);
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
var wt, Tt, Et = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, Dt = [];
Z(function() {
	wt = this.N;
})();
function Q(e, t) {
	f[e] = t.bind(null, f[e] || function() {});
}
function Ot(e) {
	if (Tt) {
		var t = Tt;
		Tt = void 0, t();
	}
	Tt = e && e.S();
}
function kt(e) {
	var t = this, n = e.data, r = jt(n);
	r.name = "ReactiveDom", r.value = n;
	var i = Le(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = bt(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = bt(function() {
			return !Array.isArray(i.value) && !m(i.value);
		}), o = Z(function() {
			if (this.N = Pt, a.value) {
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
kt.displayName = "ReactiveTextNode", Object.defineProperties(J.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: kt
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
}), Q("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof J && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), Q("__r", function(e, t) {
	if (e(t), t.type !== M) {
		Ot();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return Z(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				Et && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), Ot(n);
	}
}), Q("__e", function(e, t, n, r) {
	Ot(), e(t, n, r);
}), Q("diffed", function(e, t) {
	Ot();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = At(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function At(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = gt(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: Z(function() {
			this.N = Pt;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
Q("unmount", function(e, t) {
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
}), Q("__h", function(e, t, n, r) {
	r < 3 && (t.__$f |= 2), e(t, n, r);
}), N.prototype.shouldComponentUpdate = function(e, t) {
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
function jt(e, t) {
	return Le(function() {
		return gt(e, t);
	}, []);
}
var Mt = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function Nt() {
	ot(function() {
		for (var e; e = Dt.shift();) wt.call(e);
	});
}
function Pt() {
	Dt.push(this) === 1 && (f.requestAnimationFrame || Mt)(Nt);
}
//#endregion
//#region src/state/quality-goals.ts
var Ft = "/api/quality-goals?limit=200", It = {
	data: null,
	error: ""
}, Lt = gt(It), Rt = 0, zt = bt(() => Lt.value);
bt(() => Lt.value.data?.total ?? null);
function Bt() {
	Rt += 1, Lt.value = It;
}
async function Vt(e) {
	let t = Rt += 1;
	try {
		let n = await I(Ft, e);
		return t === Rt && (Lt.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === Rt && (Lt.value = {
			data: null,
			error: F(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var Ht = (e, t) => Vt(t), Ut = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function Wt({ openItem: e, javTitleHtml: n, javDisplayName: i, srcBadge: a }) {
	let { data: o, error: s } = zt.value;
	if (s) return /* @__PURE__ */ W("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: r(s, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let d = o?.items ?? [];
	return d.length ? /* @__PURE__ */ W("div", {
		class: "qualitylist",
		children: d.map((t) => /* @__PURE__ */ W("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ W("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${i(t)}`,
				onClick: () => e(t.id),
				children: /* @__PURE__ */ W("img", {
					src: Ut(t),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ W("div", { children: [
				/* @__PURE__ */ W("h3", { children: /* @__PURE__ */ W("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => e(t.id),
					dangerouslySetInnerHTML: { __html: n(t) }
				}) }),
				/* @__PURE__ */ W("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ W("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: a(t.location, t.cost) }
						}),
						/* @__PURE__ */ W("span", { children: c[t.location] ?? t.location }),
						/* @__PURE__ */ W("span", { children: l(t.duration) }),
						/* @__PURE__ */ W("span", { children: u(t.size ?? 0) })
					]
				}),
				t.reason ? /* @__PURE__ */ W("p", { children: t.reason }) : null
			] })]
		}, t.id))
	}) : /* @__PURE__ */ W("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: t("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/jobs.ts
async function Gt(e) {
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
function Kt(e) {
	let t = document.createElement("div");
	e.host.hidden = !0, t.dataset.followJob = "", t.setAttribute("aria-live", "polite"), e.host.prepend(t);
	let n = e.storageKey || "peach-follow-job", r = sessionStorage.getItem(n) || void 0, i = !1;
	Gt({
		read: e.read,
		active: () => !i && e.active() && t.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (a) => {
			let o = a.status === "running";
			if (e.host.hidden = !o, e.busy(o), o) {
				r = a.job_id, r && sessionStorage.setItem(n, r);
				let i = a.current, o = (i?.attempt || 1) > 1 ? ` · 第 ${i?.attempt}/${i?.max_attempts} 次尝试${i?.retry_in ? `，${i.retry_in} 秒后重试` : ""}` : "", s = (e.title || (a.total ? `${a.older ? "抓取历史" : "检查更新"}：已完成 ${a.checked || 0}/${a.total} 个来源` : "正在准备检查任务…")) + (i ? ` · ${i.label || i.provider || ""}${o}` : ""), c = e.loading(s) + ((a.total || 0) > 0 ? e.progress(a.checked || 0, a.total) : "");
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
var qt = (e, t) => I("/api/scraping", t);
function Jt({ value: e, onChange: t }) {
	let n = U(null), r = U(t);
	return r.current = t, H(() => {
		let t = n.current;
		t.innerHTML = i([
			["environment", "系统代理"],
			["direct", "应用直连"],
			["proxy", "自定义代理"]
		], e, { label: "连接方式" });
		let a = s(t.firstElementChild), o = () => r.current(a.value);
		return a.addEventListener("change", o), () => {
			a.disabled = !0, a.removeEventListener("change", o), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ W("div", {
		ref: n,
		class: "scraping-network"
	});
}
function Yt({ source: e, toast: t }) {
	let [i, a] = V(e), [s, c] = V(e.network), [l, u] = V(""), [d, f] = V(""), [p, m] = V(""), [h, g] = V("paste"), [_, v] = V(""), [y, b] = V(!1), [x, S] = V(""), [C, w] = V([]), T = U(null), E = U(null);
	H(() => {
		E.current?.querySelectorAll("footer button").forEach((e) => o(e, y));
	}, [y]);
	let D = U(new AbortController());
	Ie(() => () => D.current.abort(), []);
	async function O(n) {
		if (!y) {
			b(!0), S(""), w([]);
			try {
				if (n === "check") {
					let t = await L("/api/scraping/check", { source: e.source }, "POST", D.current.signal);
					D.current.signal.aborted || w(t.results);
				} else {
					let r = await L("/api/scraping/settings", {
						source: e.source,
						network: s,
						proxy: l,
						cookie: d,
						cookies_text: p,
						revoke: n === "revoke"
					}, "POST", D.current.signal);
					D.current.signal.aborted || (a(r.saved), u(""), f(""), m(""), v(""), T.current && (T.current.value = ""), t(n === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				D.current.signal.aborted || S(F(e));
			} finally {
				D.current.signal.aborted || b(!1);
			}
		}
	}
	return /* @__PURE__ */ W("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ W("form", {
			ref: E,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), O("save");
			},
			children: [/* @__PURE__ */ W("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ W("div", { dangerouslySetInnerHTML: { __html: n(`scraping-${e.source}`, e.label) } }),
					/* @__PURE__ */ W("a", {
						class: "scraping-url",
						href: e.login,
						target: "_blank",
						rel: "noopener noreferrer",
						children: e.login
					}),
					/* @__PURE__ */ W("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ W(Jt, {
							value: s,
							onChange: c
						})]
					}),
					s === "proxy" && /* @__PURE__ */ W("label", { children: ["代理地址", /* @__PURE__ */ W("input", {
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: l,
						placeholder: i.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						disabled: y,
						onInput: (e) => u(e.currentTarget.value)
					})] }),
					e.accepts_cookie && /* @__PURE__ */ W(M, { children: [
						/* @__PURE__ */ W("p", { children: i.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ W("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ W("label", { children: [/* @__PURE__ */ W("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: h === t,
								onChange: () => {
									g(t), f(""), m(""), v("");
								}
							}), /* @__PURE__ */ W("span", { children: n })] }, t))
						}),
						h === "paste" ? /* @__PURE__ */ W("label", { children: ["Cookie", /* @__PURE__ */ W("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: d,
							disabled: y,
							onInput: (e) => f(e.currentTarget.value)
						})] }) : /* @__PURE__ */ W("label", {
							class: "scraping-file",
							children: ["Netscape Cookie 文件（.txt）", /* @__PURE__ */ W("span", {
								class: "scraping-file-control",
								children: [
									/* @__PURE__ */ W("span", {
										class: "geist-button",
										children: "选择文件"
									}),
									/* @__PURE__ */ W("span", {
										class: "scraping-file-name",
										children: _ || "未选择文件"
									}),
									/* @__PURE__ */ W("input", {
										ref: T,
										type: "file",
										accept: ".txt",
										disabled: y,
										onChange: async (e) => {
											let t = e.currentTarget.files?.[0];
											if (!t) {
												m(""), v("");
												return;
											}
											if (m(""), t.size > 262144) {
												S("Cookie 文本超过 256 KiB"), e.currentTarget.value = "";
												return;
											}
											b(!0);
											try {
												let e = await t.text();
												D.current.signal.aborted || (m(e), v(t.name));
											} catch {
												D.current.signal.aborted || S("Cookie 文件未读取，请重新选择");
											} finally {
												D.current.signal.aborted || b(!1);
											}
										}
									})
								]
							})]
						})
					] }),
					x && /* @__PURE__ */ W("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: r(x, { variant: "error" }) }
					}),
					C.map((t) => /* @__PURE__ */ W("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: r(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ W("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					/* @__PURE__ */ W("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					}),
					/* @__PURE__ */ W("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void O("check"),
						children: "检查连接"
					}),
					e.accepts_cookie && i.cookie_saved && /* @__PURE__ */ W("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void O("revoke"),
						children: "撤销 Cookie"
					})
				]
			})]
		})
	});
}
function Xt({ data: e, error: t, toast: i }) {
	let [a, s] = V(""), [c, l] = V(!1), [u, d] = V(""), f = U(null);
	H(() => o(f.current, c), [c]);
	let p = U(new AbortController()), m = U(0);
	async function h(e = !1) {
		let t = ++m.current;
		await Gt({
			read: (e) => I("/api/scraping/cover", e),
			active: () => !p.current.signal.aborted && t === m.current,
			render: (t) => {
				l(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && d(t.error || "采集未取得"), t.status === "complete" && !e && i(t.result || "封面采集完成");
			},
			disconnected: () => d("连接中断，正在重新读取后台进度")
		});
	}
	Ie(() => (h(!0), () => p.current.abort()), []);
	async function g() {
		if (!c) {
			m.current++, l(!0), d("");
			try {
				await L("/api/scraping/cover", { code: a }, "POST", p.current.signal), await h();
			} catch (e) {
				p.current.signal.aborted || (l(!1), d(F(e)));
			}
		}
	}
	return t ? /* @__PURE__ */ W("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: r(t, { variant: "error" }) }
	}) : /* @__PURE__ */ W("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ W("p", { children: "高清图片可能需要代理才能下载，请先检查连接。" }),
			/* @__PURE__ */ W("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ W("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ W("div", { dangerouslySetInnerHTML: { __html: n("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ W("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), g();
							},
							children: [/* @__PURE__ */ W("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: a,
								disabled: c,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => s(e.currentTarget.value)
							}), /* @__PURE__ */ W("button", {
								ref: f,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						u && /* @__PURE__ */ W("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: r(u, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ W(Yt, {
				source: e,
				toast: i
			}, e.source))
		]
	});
}
//#endregion
//#region src/state/index.ts
var Zt = { "quality-goals": {
	refresh: Vt,
	reset: Bt
} }, Qt = () => Object.keys(Zt);
async function $t(e) {
	let t = Zt[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/native-image.ts
function en(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function tn(e, t, n, r, i = 1) {
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
function nn(e, t) {
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
//#region src/sidebar.ts
function rn(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function an(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function on(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function sn(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function cn(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function ln() {
	return `<div class="cleanuppage" data-skeleton="cleanup" aria-busy="true" aria-label="正在读取数据管理状态">
    <div class="cleanupgrid">${[
		[
			"采集来源",
			"设置采集来源",
			"下载高清封面，设置代理和 Cookie。"
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
function un(e, t = !1, n = !1) {
	if (t || n) return "";
	let r = "<svg aria-hidden=\"true\"><use href=\"#i-external-link\"></use></svg>";
	return `<details class="taste-history-guide"${e ? " open" : ""}>
    <summary>浏览器历史记录导入指南</summary>
    <div class="taste-history-guide-content">
      <p>在运行 Peach 的电脑上使用浏览器：点击上方「读取 Peach 主机」。</p>
      <p>记录在其他设备上：导出文件后，点击上方「导入历史」。多台设备的文件分别导入。</p>
      <ul><li>Chrome：在 <a href="https://takeout.google.com/" target="_blank" rel="noreferrer">Google Takeout${r}</a> 选择 Chrome 历史记录，下载 ZIP 后直接导入。</li>
      <li>其他浏览器：使用 <a href="https://github.com/purarue/browserexport" target="_blank" rel="noreferrer">browserexport${r}</a> 导出历史记录，再导入导出文件。</li></ul>
      <p>需要刷新时再次读取或导入；数据源可在页面底部移除。</p>
      <button type="button" class="taste-guide-skip">跳过</button>
    </div></details>`;
}
var dn = "peach-taste-guide-dismissed";
function fn(e, t) {
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(dn, "1"), n.remove();
	});
}
//#endregion
//#region src/jav-artwork.ts
function pn(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function mn(e) {
	return {
		javLayout: pn(e.javLayout),
		javImage: hn(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function hn(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function gn(e, t) {
	return e.is_jav && e.code && e.has_cover && (hn(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function _n(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (hn(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.removeAttribute("style"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var vn = {
	scraping: {
		load: qt,
		component: Xt
	},
	"quality-goals": {
		load: Ht,
		component: Wt
	},
	configuration: {
		load: Ze,
		component: rt
	}
}, yn = () => Object.keys(vn), $ = /* @__PURE__ */ new Map();
async function bn(e, t, n, r = {}) {
	let i = vn[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	xn(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	$.set(t, a);
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
			error: F(e)
		};
	}
	if ($.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		$.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	xe(te(i.component, s), t);
}
function xn(e) {
	let t = $.get(e);
	t && (t.controller.abort(), $.delete(e), t.painted && xe(null, e));
}
//#endregion
export { dn as TASTE_GUIDE_KEY, ln as cleanupSkeletonHtml, sn as cloudLocations, cn as cloudPreferenceLocations, nn as entitySkeletonHtml, Kt as followJobProgress, yn as islandNames, gn as javImageKind, en as matchesFaceSource, bn as mountIsland, tn as nativeImageFit, hn as normalizeJavImage, pn as normalizeJavLayout, mn as normalizeJavPreferences, $t as refreshStore, rn as sidebarHasCatalogContent, on as sidebarTagCounts, Qt as storeNames, _n as syncJavImages, an as syncSidebarSurface, un as tasteHistoryGuideHtml, xn as unmountIsland, Gt as watchJob, fn as wireTasteHistoryGuide };
