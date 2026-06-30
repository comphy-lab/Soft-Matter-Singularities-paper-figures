/**
Sample velocity magnitude and Newtonian dissipation density from a Basilisk
snapshot for the c1024 Newtonian pinch-off case.

Output columns on stderr:
  x y vel log10_diss

The dissipation density is Phi = 2 mu(f) D:D with
mu(f) = Oh*f + Oha*(1 - f).  For c1024, Oh=1e-2 and Oha=1e-4 are passed on
the command line.
*/

#include "utils.h"
#include "output.h"

scalar f[];
vector u[];

char filename[256];
int nx, ny, len;
double xmin, ymin, xmax, ymax, Deltax, Deltay;
double Oh = 1e-2, Oha = 1e-4;

scalar vel[], logDiss[];
scalar * list = NULL;

int main(int a, char const *arguments[])
{
  if (a < 7) {
    fprintf(ferr, "Usage: %s snapshot xmin ymin xmax ymax ny [Oh Oha]\n", arguments[0]);
    return 1;
  }

  sprintf(filename, "%s", arguments[1]);
  xmin = atof(arguments[2]); ymin = atof(arguments[3]);
  xmax = atof(arguments[4]); ymax = atof(arguments[5]);
  ny = atoi(arguments[6]);
  if (a > 7) Oh = atof(arguments[7]);
  if (a > 8) Oha = atof(arguments[8]);

  list = list_add(list, vel);
  list = list_add(list, logDiss);

  restore(file = filename);

  foreach() {
    double Drr = (u.y[0,1] - u.y[0,-1])/(2.*Delta);
    double Dtt = (fabs(y) > 1e-14 ? u.y[]/y : 0.);
    double Dzz = (u.x[1,0] - u.x[-1,0])/(2.*Delta);
    double Drz = 0.5*((u.y[1,0] - u.y[-1,0] + u.x[0,1] - u.x[0,-1])/(2.*Delta));
    double DD = sq(Drr) + sq(Dtt) + sq(Dzz) + 2.*sq(Drz);
    double mu_local = Oh*f[] + Oha*(1. - f[]);
    double phi = 2.*mu_local*DD;

    vel[] = sqrt(sq(u.x[]) + sq(u.y[]));
    logDiss[] = phi > 0. ? log(phi)/log(10.) : -99.;
  }

  Deltay = (double)((ymax - ymin)/ny);
  nx = (int)((xmax - xmin)/Deltay);
  if (nx < 2) nx = 2;
  Deltax = (double)((xmax - xmin)/nx);
  len = list_len(list);

  double ** field = (double **) matrix_new(nx, ny + 1, len*sizeof(double));
  for (int i = 0; i < nx; i++) {
    double x = Deltax*(i + 0.5) + xmin;
    for (int j = 0; j < ny; j++) {
      double y = Deltay*(j + 0.5) + ymin;
      int k = 0;
      for (scalar s in list)
        field[i][len*j + k++] = interpolate(s, x, y);
    }
  }

  FILE * fp = ferr;
  for (int i = 0; i < nx; i++) {
    double x = Deltax*(i + 0.5) + xmin;
    for (int j = 0; j < ny; j++) {
      double y = Deltay*(j + 0.5) + ymin;
      fprintf(fp, "%g %g", x, y);
      int k = 0;
      for (scalar s in list)
        fprintf(fp, " %g", field[i][len*j + k++]);
      fputc('\n', fp);
    }
  }
  fflush(fp);
  fclose(fp);
  matrix_free(field);
}
