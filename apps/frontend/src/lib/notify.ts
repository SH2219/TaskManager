import { toast, type Id, type ToastOptions } from "react-toastify";

const defaults: ToastOptions = {
  position: "top-right",
  autoClose: 3200,
  hideProgressBar: false,
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
};

export const notify = {
  success(message: string, options?: ToastOptions): Id {
    return toast.success(message, { ...defaults, ...options });
  },
  error(message: string, options?: ToastOptions): Id {
    return toast.error(message, { ...defaults, autoClose: 4500, ...options });
  },
  info(message: string, options?: ToastOptions): Id {
    return toast.info(message, { ...defaults, ...options });
  },
  fromError(err: unknown, fallback = "Something went wrong"): Id {
    const message = err instanceof Error && err.message ? err.message : fallback;
    return this.error(message);
  },
};
